import os

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from logic.detector import detect_fall


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("跌倒检测系统")
        self.setGeometry(100, 100, 600, 400)
        self.file_path = None

        self.file_label = QLabel("未选择文件")
        self.model_label = QLabel("选择模型：")
        self.model_selector = QComboBox()
        self.populate_model_selector()

        self.select_button = QPushButton("选择图片或视频")
        self.detect_button = QPushButton("开始检测")
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        self.check_person = QCheckBox("启用无人帧筛除")
        self.check_static = QCheckBox("启用静态帧筛除")

        self.frame_skip_label = QLabel("每几帧检测一次：")
        self.frame_skip_spinbox = QSpinBox()
        self.frame_skip_spinbox.setRange(1, 30)
        self.frame_skip_spinbox.setValue(1)
        self.frame_skip_spinbox.setToolTip("推荐设置为 2，以提升效率")

        layout = QVBoxLayout()
        layout.addWidget(self.file_label)

        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_selector)
        layout.addLayout(model_layout)

        layout.addWidget(self.select_button)
        layout.addWidget(self.detect_button)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.check_person)
        filter_layout.addWidget(self.check_static)
        layout.addLayout(filter_layout)

        frame_skip_layout = QHBoxLayout()
        frame_skip_layout.addWidget(self.frame_skip_label)
        frame_skip_layout.addWidget(self.frame_skip_spinbox)
        layout.addLayout(frame_skip_layout)

        layout.addWidget(QLabel("检测日志："))
        layout.addWidget(self.log_area)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.select_button.clicked.connect(self.select_file)
        self.detect_button.clicked.connect(self.start_detection)

    def populate_model_selector(self):
        assets_dir = "assets"
        if not os.path.exists(assets_dir):
            return
        for folder in sorted(os.listdir(assets_dir)):
            model_path = os.path.join(assets_dir, folder, "best.pt")
            if os.path.isfile(model_path):
                self.model_selector.addItem(f"{folder}/best.pt")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图像或视频",
            "",
            "图像和视频文件 (*.jpg *.jpeg *.png *.mp4 *.avi *.mov *.mkv)",
        )
        if file_path:
            self.file_path = file_path
            self.file_label.setText(f"已选择文件：{file_path}")

    def start_detection(self):
        if not self.file_path:
            self.log_area.append("请先选择文件。")
            return

        model_name = self.model_selector.currentText()
        if not model_name:
            self.log_area.append("请先选择模型。")
            return

        model_path = os.path.join("assets", model_name)
        output_subdir = model_name.split("/")[0]
        self.log_area.clear()
        self.log_area.append("开始检测...\n")

        result_path = detect_fall(
            path=self.file_path,
            model_path=model_path,
            output_subdir=output_subdir,
            use_filter_person=self.check_person.isChecked(),
            use_filter_static=self.check_static.isChecked(),
            log_area=self.log_area,
            frame_interval=self.frame_skip_spinbox.value(),
        )

        if result_path:
            self.log_area.append(f"\n结果已保存至：{result_path}")
        else:
            self.log_area.append("检测失败，请检查输入文件。")
