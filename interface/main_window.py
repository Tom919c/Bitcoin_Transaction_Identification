"""
PyQt主窗口
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt
import torch

from .data_loader import load_data, load_model, predict
from data.utils import LABEL_MAP_INV


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.data = None
        self.model = None
        self.predictions = None

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('比特币交易节点分类系统')
        self.setGeometry(100, 100, 1200, 800)

        # 主widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 工具栏
        toolbar = QHBoxLayout()

        self.btn_load_data = QPushButton('加载数据')
        self.btn_load_data.clicked.connect(self.load_data_file)
        toolbar.addWidget(self.btn_load_data)

        self.btn_load_model = QPushButton('加载模型')
        self.btn_load_model.clicked.connect(self.load_model_file)
        toolbar.addWidget(self.btn_load_model)

        self.btn_predict = QPushButton('执行预测')
        self.btn_predict.clicked.connect(self.run_prediction)
        self.btn_predict.setEnabled(False)
        toolbar.addWidget(self.btn_predict)

        toolbar.addStretch()

        self.label_status = QLabel('状态: 未加载数据')
        toolbar.addWidget(self.label_status)

        layout.addLayout(toolbar)

        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 结果表格标签页
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(
            ['节点ID', '真实标签', '预测标签', '预测概率', '是否正确']
        )
        self.tabs.addTab(self.table_widget, '预测结果')

        # 统计信息标签页
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        self.stats_label = QLabel('请先加载数据和模型，然后执行预测')
        self.stats_layout.addWidget(self.stats_label)
        self.tabs.addTab(self.stats_widget, '统计信息')

    def load_data_file(self):
        """加载数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择数据文件', '', 'PyTorch文件 (*.pt)'
        )
        if file_path:
            try:
                self.data = load_data(file_path)
                self.label_status.setText(
                    f'状态: 已加载数据 (节点数: {self.data.num_nodes}, 边数: {self.data.num_edges})'
                )
                self.check_ready()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'加载数据失败: {e}')

    def load_model_file(self):
        """加载模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择模型文件', '', 'PyTorch文件 (*.pt)'
        )
        if file_path:
            try:
                # TODO: 需要根据实际情况选择模型类和配置
                from models import get_model
                # 这里需要用户选择模型类型或从配置文件读取
                QMessageBox.information(
                    self, '提示',
                    '模型加载需要配置文件支持，请确保配置正确'
                )
            except Exception as e:
                QMessageBox.critical(self, '错误', f'加载模型失败: {e}')

    def check_ready(self):
        """检查是否可以执行预测"""
        self.btn_predict.setEnabled(self.data is not None and self.model is not None)

    def run_prediction(self):
        """执行预测"""
        if self.data is None or self.model is None:
            return

        try:
            self.predictions = predict(self.model, self.data)
            self.update_table()
            self.update_stats()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'预测失败: {e}')

    def update_table(self):
        """更新结果表格"""
        if self.predictions is None:
            return

        preds = self.predictions['predictions']
        probs = self.predictions['probabilities']
        true_labels = self.data.y

        # 只显示测试集结果
        test_mask = self.data.test_mask
        test_indices = torch.where(test_mask)[0]

        self.table_widget.setRowCount(len(test_indices))

        for i, idx in enumerate(test_indices[:1000]):  # 限制显示数量
            idx = idx.item()
            true_label = true_labels[idx].item()
            pred_label = preds[idx].item()
            prob = probs[idx][pred_label].item()
            correct = true_label == pred_label

            self.table_widget.setItem(i, 0, QTableWidgetItem(str(idx)))
            self.table_widget.setItem(i, 1, QTableWidgetItem(LABEL_MAP_INV.get(true_label, 'UNKNOWN')))
            self.table_widget.setItem(i, 2, QTableWidgetItem(LABEL_MAP_INV.get(pred_label, 'UNKNOWN')))
            self.table_widget.setItem(i, 3, QTableWidgetItem(f'{prob:.4f}'))
            self.table_widget.setItem(i, 4, QTableWidgetItem('✓' if correct else '✗'))

    def update_stats(self):
        """更新统计信息"""
        if self.predictions is None:
            return

        from training.evaluator import compute_metrics

        metrics = compute_metrics(
            self.predictions['logits'],
            self.data.y,
            self.data.test_mask
        )

        stats_text = f"""
        测试集评估结果:

        准确率: {metrics['accuracy']:.4f}
        Macro F1: {metrics['macro_f1']:.4f}
        Micro F1: {metrics['micro_f1']:.4f}
        Weighted F1: {metrics['weighted_f1']:.4f}

        各类别F1分数:
        """

        label_names = ['NONE', 'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'BRIDGE']
        for i, name in enumerate(label_names):
            if i < len(metrics['per_class_f1']):
                stats_text += f"\n        {name}: {metrics['per_class_f1'][i]:.4f}"

        self.stats_label.setText(stats_text)


def run_app():
    """运行应用"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
