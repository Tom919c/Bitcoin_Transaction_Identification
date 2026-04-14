"""
GraphSAGE 参数调优脚本。

说明：
- 仅调优 GraphSAGE（models/sage.py）。
- 通过配置中的 tuning.space 定义离散搜索空间。
- 支持 random/grid 两种搜索方式。
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import os
import random
import sys
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import yaml
import torch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.build_graph import load_data
from models import get_model
from training import Trainer
from training.utils import set_seed


MODEL_PARAM_KEYS = {'hidden_channels', 'num_layers', 'dropout'}
TRAIN_PARAM_KEYS = {
    'epochs',
    'lr',
    'weight_decay',
    'batch_size',
    'neighbor_sizes',
    'loss',
    'focal_gamma',
    'class_weight_power',
    'class_weight_cap',
    'grad_clip_norm',
    'scheduler',
    'scheduler_step_size',
    'scheduler_gamma',
    'scheduler_factor',
    'scheduler_patience',
    'early_stopping_patience',
}


def _normalize_space(space: Dict[str, Any]) -> Dict[str, List[Any]]:
    normalized: Dict[str, List[Any]] = {}
    for key, value in space.items():
        if isinstance(value, list):
            if not value:
                raise ValueError(f"tuning.space.{key} 不能为空列表")
            normalized[key] = value
        else:
            normalized[key] = [value]
    if not normalized:
        raise ValueError("tuning.space 不能为空")
    return normalized


def _grid_candidates(space: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    keys = list(space.keys())
    values = [space[key] for key in keys]
    return [
        {key: copy.deepcopy(val) for key, val in zip(keys, combo)}
        for combo in itertools.product(*values)
    ]


def _random_candidates(
    space: Dict[str, List[Any]],
    max_trials: int,
    seed: int
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    keys = list(space.keys())
    results: List[Dict[str, Any]] = []
    seen = set()
    max_attempts = max(100, max_trials * 50)

    attempts = 0
    while len(results) < max_trials and attempts < max_attempts:
        attempts += 1
        candidate = {}
        for key in keys:
            candidate[key] = copy.deepcopy(rng.choice(space[key]))
        signature = json.dumps(candidate, sort_keys=True, ensure_ascii=False)
        if signature in seen:
            continue
        seen.add(signature)
        results.append(candidate)
    return results


def _build_candidates(
    strategy: str,
    space: Dict[str, List[Any]],
    max_trials: int,
    seed: int
) -> List[Dict[str, Any]]:
    strategy = strategy.lower()
    if strategy == 'grid':
        all_candidates = _grid_candidates(space)
        return all_candidates[:max_trials]
    if strategy == 'random':
        return _random_candidates(space, max_trials=max_trials, seed=seed)
    raise ValueError("tuning.strategy 仅支持 random / grid")


def _apply_candidate(base_config: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    cfg = copy.deepcopy(base_config)
    cfg.setdefault('model', {})
    cfg.setdefault('train', {})
    cfg['model']['name'] = 'sage'
    cfg['model'].setdefault('params', {})

    for key, value in candidate.items():
        if key in MODEL_PARAM_KEYS:
            cfg['model']['params'][key] = copy.deepcopy(value)
        elif key in TRAIN_PARAM_KEYS:
            cfg['train'][key] = copy.deepcopy(value)
        else:
            raise ValueError(f"未识别的调参字段: {key}")

    # 调参过程中不应默认复用断点续训
    cfg['train']['resume_from_checkpoint'] = None
    return cfg


def _setup_wandb_for_trial(
    trial_config: Dict[str, Any],
    trial_index: int,
    trial_seed: int
):
    wandb_config = trial_config.get('wandb', {})
    enabled = bool(wandb_config.get('enabled', False))
    mode = str(wandb_config.get('mode', 'online'))
    if not enabled or mode == 'disabled':
        return None

    try:
        import wandb
    except ImportError as exc:
        raise ImportError("已启用wandb但未安装，请先执行: pip install wandb") from exc

    base_name = wandb_config.get('run_name') or 'sage-tuning'
    run_name = f"{base_name}-trial{trial_index:03d}-seed{trial_seed}"

    run = wandb.init(
        project=wandb_config.get('project', 'bitcoin-transaction-identification'),
        entity=wandb_config.get('entity'),
        mode=mode,
        name=run_name,
        reinit=True,
        config={
            'tuning_trial': trial_index,
            'tuning_seed': trial_seed,
            'model': trial_config.get('model', {}),
            'train': trial_config.get('train', {})
        }
    )
    return run


def _run_single_experiment(
    trial_config: Dict[str, Any],
    base_data,
    use_mini_batch: bool,
    trial_index: int,
    trial_seed: int,
    trial_checkpoint_dir: str
) -> Dict[str, Any]:
    set_seed(trial_seed)
    data = base_data.clone()
    trial_cfg = copy.deepcopy(trial_config)
    trial_cfg.setdefault('train', {})
    trial_cfg['train']['checkpoint_dir'] = trial_checkpoint_dir
    trial_cfg['train']['resume_from_checkpoint'] = None

    model_cfg = trial_cfg.get('model', {})
    model = get_model(
        name=model_cfg.get('name', 'sage'),
        in_channels=data.num_features,
        out_channels=trial_cfg.get('data', {}).get('num_classes', 6),
        **model_cfg.get('params', {})
    )

    wandb_run = _setup_wandb_for_trial(trial_cfg, trial_index, trial_seed)
    trainer = Trainer(model, data, trial_cfg, wandb_run=wandb_run)

    effective_mini_batch = bool(use_mini_batch)
    try:
        try:
            trainer.train(use_mini_batch=effective_mini_batch)
        except ImportError as exc:
            if effective_mini_batch and "NeighborSampler" in str(exc):
                print("检测到缺少 NeighborSampler 后端（pyg-lib/torch-sparse），自动回退到全图训练。")
                print("若要启用 mini-batch，请安装 pyg-lib 或 torch-sparse。")
                effective_mini_batch = False
                trainer.train(use_mini_batch=False)
            else:
                raise
        if trainer.train_log:
            best_entry = max(trainer.train_log, key=lambda row: float(row.get('val_f1', 0.0)))
            best_val_f1 = float(best_entry.get('val_f1', 0.0))
            best_epoch = int(best_entry.get('epoch', 0))
        else:
            best_val_f1 = 0.0
            best_epoch = 0

        val_metrics = trainer.evaluate(data.val_mask)
        test_metrics = trainer.evaluate(data.test_mask)

        result = {
            'seed': trial_seed,
            'use_mini_batch': effective_mini_batch,
            'best_val_f1': best_val_f1,
            'best_epoch': best_epoch,
            'final_val_f1': float(val_metrics.get('macro_f1', 0.0)),
            'final_test_f1': float(test_metrics.get('macro_f1', 0.0)),
            'best_checkpoint_path': os.path.join(trial_checkpoint_dir, 'best_model.pt')
        }
        if wandb_run is not None:
            wandb_run.summary.update(result)
        return result
    finally:
        if wandb_run is not None:
            wandb_run.finish()
        del trainer
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def _aggregate_trial(
    trial_index: int,
    params: Dict[str, Any],
    per_seed_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    best_scores = [item['best_val_f1'] for item in per_seed_results]
    final_val_scores = [item['final_val_f1'] for item in per_seed_results]
    final_test_scores = [item['final_test_f1'] for item in per_seed_results]

    return {
        'trial': trial_index,
        'params': params,
        'seed_results': per_seed_results,
        'mean_best_val_f1': float(np.mean(best_scores)),
        'std_best_val_f1': float(np.std(best_scores)),
        'mean_final_val_f1': float(np.mean(final_val_scores)),
        'mean_final_test_f1': float(np.mean(final_test_scores)),
    }


def _save_json(path: str, payload: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _atomic_save_json(path: str, payload: Any):
    target_dir = os.path.dirname(path)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix='.tmp_tuning_', suffix='.json', dir=target_dir or '.')
    os.close(fd)
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _make_progress_signature(
    strategy: str,
    max_trials: int,
    use_mini_batch: bool,
    sampling_seed: int,
    trial_seeds: List[int],
    space: Dict[str, List[Any]],
    data_path: str
) -> str:
    payload = {
        'strategy': strategy,
        'max_trials': max_trials,
        'use_mini_batch': bool(use_mini_batch),
        'sampling_seed': int(sampling_seed),
        'trial_seeds': list(trial_seeds),
        'space': space,
        'data_path': data_path
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _init_or_load_progress(
    progress_path: str,
    resume_enabled: bool,
    signature: str,
    candidates: List[Dict[str, Any]],
    trial_seeds: List[int]
) -> Dict[str, Any]:
    if resume_enabled and os.path.exists(progress_path):
        with open(progress_path, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        if progress.get('signature') != signature:
            raise ValueError(
                "检测到调参进度文件与当前配置不匹配。"
                "如需重跑，请删除旧进度文件或关闭 resume。"
            )
        return progress

    progress = {
        'version': 1,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'updated_at': datetime.now().isoformat(timespec='seconds'),
        'signature': signature,
        'trial_seeds': list(trial_seeds),
        'candidates': candidates,
        'trials': {}
    }
    _atomic_save_json(progress_path, progress)
    return progress


def _resolve_tuning_config(config: Dict[str, Any], args) -> Dict[str, Any]:
    tuning_cfg = copy.deepcopy(config.get('tuning', {}))
    if args.strategy:
        tuning_cfg['strategy'] = args.strategy
    if args.max_trials is not None:
        tuning_cfg['max_trials'] = args.max_trials
    if args.output_dir:
        tuning_cfg['output_dir'] = args.output_dir
    if args.mini_batch:
        tuning_cfg['use_mini_batch'] = True
    if args.progress_file:
        tuning_cfg['progress_file'] = args.progress_file
    if args.resume:
        tuning_cfg['resume'] = True
    if args.no_resume:
        tuning_cfg['resume'] = False
    if args.start_trial is not None:
        tuning_cfg['start_trial'] = args.start_trial
    if args.end_trial is not None:
        tuning_cfg['end_trial'] = args.end_trial
    if args.seeds:
        parsed_seeds: List[int] = []
        for token in str(args.seeds).split(','):
            token = token.strip()
            if not token:
                continue
            try:
                parsed_seeds.append(int(token))
            except ValueError as exc:
                raise ValueError(f"--seeds 参数非法: {args.seeds}") from exc
        if not parsed_seeds:
            raise ValueError("--seeds 不能为空，例如: --seeds 42 或 --seeds 42,3407")
        tuning_cfg['seeds'] = parsed_seeds
    return tuning_cfg


def main():
    parser = argparse.ArgumentParser(description='GraphSAGE超参数调优')
    parser.add_argument('--config', type=str, default='config/default.yaml', help='配置文件路径')
    parser.add_argument('--strategy', type=str, default=None, choices=['random', 'grid'], help='搜索策略')
    parser.add_argument('--max-trials', type=int, default=None, help='最多尝试的参数组合数量')
    parser.add_argument('--mini-batch', action='store_true', help='强制使用mini-batch训练')
    parser.add_argument('--output-dir', type=str, default=None, help='调参结果输出目录')
    parser.add_argument('--progress-file', type=str, default=None, help='调参进度文件路径')
    parser.add_argument('--resume', action='store_true', help='强制启用断点续跑')
    parser.add_argument('--no-resume', action='store_true', help='禁用断点续跑并从头开始')
    parser.add_argument('--start-trial', type=int, default=None, help='仅执行从该序号开始的 trial（1-based）')
    parser.add_argument('--end-trial', type=int, default=None, help='仅执行到该序号结束的 trial（1-based）')
    parser.add_argument('--seeds', type=str, default=None, help='覆盖 seeds，逗号分隔，如 42 或 42,3407')
    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    tuning_cfg = _resolve_tuning_config(config, args)
    strategy = str(tuning_cfg.get('strategy', 'random'))
    max_trials = int(tuning_cfg.get('max_trials', 20))
    use_mini_batch = bool(tuning_cfg.get('use_mini_batch', True))
    output_dir = str(tuning_cfg.get('output_dir', './experiments/tuning'))
    resume_enabled = bool(tuning_cfg.get('resume', True))
    progress_path = tuning_cfg.get('progress_file')
    if progress_path:
        progress_path = str(progress_path)
    else:
        progress_path = os.path.join(output_dir, 'sage_tuning_progress.json')
    sampling_seed = int(tuning_cfg.get('seed', config.get('train', {}).get('seed', 42)))
    trial_seeds = tuning_cfg.get('seeds', [config.get('train', {}).get('seed', 42)])
    trial_seeds = [int(seed) for seed in trial_seeds]
    if not trial_seeds:
        raise ValueError("tuning.seeds 不能为空")

    space = _normalize_space(tuning_cfg.get('space', {}))
    candidates = _build_candidates(strategy, space, max_trials=max_trials, seed=sampling_seed)
    if not candidates:
        raise ValueError("未生成任何候选参数组合，请检查 tuning.space 或 max_trials")
    total_candidates = len(candidates)

    start_trial = int(tuning_cfg.get('start_trial', 1))
    end_trial_cfg = tuning_cfg.get('end_trial', None)
    end_trial = int(end_trial_cfg) if end_trial_cfg is not None else total_candidates
    if start_trial < 1:
        raise ValueError("start_trial 必须 >= 1")
    if start_trial > total_candidates:
        raise ValueError(f"start_trial={start_trial} 超出候选数量 {total_candidates}")
    if end_trial < start_trial:
        raise ValueError("end_trial 不能小于 start_trial")
    end_trial = min(end_trial, total_candidates)
    selected_trials: List[Tuple[int, Dict[str, Any]]] = [
        (idx, candidates[idx - 1]) for idx in range(start_trial, end_trial + 1)
    ]
    if not selected_trials:
        raise ValueError("当前执行范围内没有可运行 trial")

    data_path = config.get('data', {}).get(
        'processed_data_path',
        'D:\\Code\\VSCode\\Bitcoin_Transaction_Identification\\data\\processed\\data.pt'
    )
    print(f"加载数据: {data_path}")
    data = load_data(data_path)
    print(f"候选组合总数: {total_candidates} | 本次执行 trial 数: {len(selected_trials)} | 每组种子数: {len(trial_seeds)}")
    print(f"执行范围: trial {start_trial} -> {end_trial}")
    print(f"调参训练模式: {'mini-batch' if use_mini_batch else 'full-batch'}")
    print(f"断点续跑: {'开启' if resume_enabled else '关闭'} | 进度文件: {progress_path}")

    progress_signature = _make_progress_signature(
        strategy=strategy,
        max_trials=max_trials,
        use_mini_batch=use_mini_batch,
        sampling_seed=sampling_seed,
        trial_seeds=trial_seeds,
        space=space,
        data_path=data_path
    )
    progress = _init_or_load_progress(
        progress_path=progress_path,
        resume_enabled=resume_enabled,
        signature=progress_signature,
        candidates=candidates,
        trial_seeds=trial_seeds
    )

    all_results: List[Dict[str, Any]] = []
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

    for idx, candidate in selected_trials:
        print(f"\n[Trial {idx}/{len(candidates)}] params = {candidate}")
        trial_key = str(idx)
        existing_trial = progress.get('trials', {}).get(trial_key, {})
        done_seed_results = existing_trial.get('seed_results', [])
        done_seed_map = {int(item['seed']): item for item in done_seed_results if 'seed' in item}

        per_seed_results: List[Dict[str, Any]] = []
        for seed in trial_seeds:
            if seed in done_seed_map:
                cached = done_seed_map[seed]
                per_seed_results.append(cached)
                print(
                    f"  seed={seed} | 已从进度恢复 best_val_f1={cached.get('best_val_f1', 0.0):.4f} "
                    f"| best_epoch={cached.get('best_epoch', 0)}"
                )
                continue

            trial_config = _apply_candidate(config, candidate)
            trial_config.setdefault('train', {})
            trial_config['train']['seed'] = seed
            trial_checkpoint_dir = os.path.join(
                output_dir,
                'checkpoints',
                f"trial_{idx:03d}_seed_{seed}"
            )

            result = _run_single_experiment(
                trial_config=trial_config,
                base_data=data,
                use_mini_batch=use_mini_batch,
                trial_index=idx,
                trial_seed=seed,
                trial_checkpoint_dir=trial_checkpoint_dir
            )
            per_seed_results.append(result)
            print(
                f"  seed={seed} | best_val_f1={result['best_val_f1']:.4f} "
                f"| best_epoch={result['best_epoch']}"
            )

            progress.setdefault('trials', {})
            partial_seed_results = [
                done_seed_map[s] for s in trial_seeds if s in done_seed_map
            ] + [
                r for r in per_seed_results if int(r.get('seed', -1)) not in done_seed_map
            ]
            progress['trials'][trial_key] = {
                'params': candidate,
                'seed_results': partial_seed_results,
                'complete': len(partial_seed_results) == len(trial_seeds)
            }
            progress['updated_at'] = datetime.now().isoformat(timespec='seconds')
            _atomic_save_json(progress_path, progress)

        aggregated = _aggregate_trial(idx, candidate, per_seed_results)
        all_results.append(aggregated)
        print(
            f"  -> mean_best_val_f1={aggregated['mean_best_val_f1']:.4f} "
            f"(std={aggregated['std_best_val_f1']:.4f})"
        )
        progress['trials'][trial_key] = {
            'params': candidate,
            'seed_results': per_seed_results,
            'aggregate': aggregated,
            'complete': True
        }
        progress['updated_at'] = datetime.now().isoformat(timespec='seconds')
        _atomic_save_json(progress_path, progress)

    ranked = sorted(all_results, key=lambda row: row['mean_best_val_f1'], reverse=True)
    best = ranked[0]
    best_config = _apply_candidate(config, best['params'])

    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, f"sage_tuning_summary_{timestamp}.json")
    ranked_path = os.path.join(output_dir, f"sage_tuning_ranked_{timestamp}.json")
    best_cfg_path = os.path.join(output_dir, f"sage_best_config_{timestamp}.yaml")

    summary_payload = {
        'strategy': strategy,
        'max_trials': len(candidates),
        'executed_start_trial': start_trial,
        'executed_end_trial': end_trial,
        'use_mini_batch': use_mini_batch,
        'seeds': trial_seeds,
        'best_trial': best,
        'ranked_top_10': ranked[:10],
    }
    _save_json(summary_path, summary_payload)
    _save_json(ranked_path, ranked)
    with open(best_cfg_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(best_config, f, allow_unicode=True, sort_keys=False)

    print("\n调参完成。")
    print(f"最佳 mean_best_val_f1: {best['mean_best_val_f1']:.4f}")
    print(f"最佳参数: {best['params']}")
    print(f"结果汇总: {summary_path}")
    print(f"完整排序: {ranked_path}")
    print(f"最佳配置导出: {best_cfg_path}")

    progress['finished_at'] = datetime.now().isoformat(timespec='seconds')
    progress['best_trial'] = best
    progress['ranked_path'] = ranked_path
    progress['summary_path'] = summary_path
    progress['best_config_path'] = best_cfg_path
    _atomic_save_json(progress_path, progress)


if __name__ == '__main__':
    main()

