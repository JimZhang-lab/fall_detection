import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Select,
  Checkbox,
  InputNumber,
  Upload,
  Spin,
  Alert,
  Divider,
  Row,
  Col,
  Space,
  message,
} from 'antd';
import {
  UploadOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import LogPanel from './LogPanel';
import './DetectionPanel.css';

const API_BASE = '/api';

export default function DetectionPanel() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [logs, setLogs] = useState([]);
  const [fileMetadata, setFileMetadata] = useState(null);
  const [detectionResult, setDetectionResult] = useState(null);
  const [uploadFileList, setUploadFileList] = useState([]);

  // Detection options
  const [useFilterPerson, setUseFilterPerson] = useState(false);
  const [useFilterStatic, setUseFilterStatic] = useState(false);
  const [frameInterval, setFrameInterval] = useState(1);

  // Load available models on mount
  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const response = await axios.get(`${API_BASE}/models`);
      setModels(response.data.models);
      if (response.data.models.length > 0) {
        setSelectedModel(response.data.models[0].path);
      }
    } catch (error) {
      message.error('Failed to load models: ' + error.message);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadedFile({
        fileId: response.data.file_id,
        name: response.data.original_filename || response.data.filename,
      });
      setFileMetadata(response.data.metadata);
      setLogs([`✓ File uploaded: ${response.data.original_filename || response.data.filename}`]);
      setDetectionResult(null);
      message.success('File uploaded successfully');
    } catch (error) {
      setUploadedFile(null);
      setFileMetadata(null);
      setDetectionResult(null);
      setUploadFileList([]);
      message.error('Upload failed: ' + (error.response?.data?.error || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDetect = async () => {
    if (!uploadedFile) {
      message.error('Please upload a file first');
      return;
    }

    if (!selectedModel) {
      message.error('Please select a model');
      return;
    }

    setDetecting(true);
    setLogs([]);
    setDetectionResult(null);

    try {
      const response = await axios.post(`${API_BASE}/detect`, {
        file_id: uploadedFile.fileId,
        model_name: selectedModel,
        use_filter_person: useFilterPerson,
        use_filter_static: useFilterStatic,
        frame_interval: frameInterval,
      });

      if (response.data.success) {
        setDetectionResult({
          resultPath: response.data.result_path,
          downloadUrl: response.data.download_url,
        });
        setLogs(response.data.logs || []);
        message.success('Detection completed successfully');
      } else {
        setLogs(response.data.logs || []);
        message.error('Detection failed: ' + response.data.error);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.message;
      const errorLogs = error.response?.data?.logs;
      if (errorLogs) {
        setLogs(errorLogs);
      }
      message.error('Detection error: ' + errorMessage);
    } finally {
      setDetecting(false);
    }
  };

  const handleClear = () => {
    setUploadedFile(null);
    setFileMetadata(null);
    setLogs([]);
    setDetectionResult(null);
    setUploadFileList([]);
  };

  const uploadProps = {
    maxCount: 1,
    accept: '.jpg,.jpeg,.png,.mp4,.avi,.mov,.mkv',
    fileList: uploadFileList,
    onRemove: () => {
      handleClear();
      return true;
    },
    beforeUpload: (file) => {
      const maxSize = 500 * 1024 * 1024; // 500MB
      if (file.size > maxSize) {
        message.error('File size exceeds 500MB limit');
        return false;
      }
      setUploadFileList([file]);
      handleFileUpload(file);
      return false; // Prevent default upload
    },
  };

  return (
    <div className="detection-panel">
      <Row gutter={[24, 24]}>
        {/* Control Panel */}
        <Col xs={24} lg={16}>
          <Card
            title="检测控制面板 (Detection Control)"
            className="shadow-lg"
            headStyle={{ background: '#1890ff', color: 'white' }}
          >
            {/* File Upload Section */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">1. 选择文件 (Select File)</h3>
              <Upload.Dragger {...uploadProps}>
                <UploadOutlined className="text-4xl text-blue-500 mb-2" />
                <p className="text-base font-semibold">点击或拖拽上传图片/视频</p>
                <p className="text-xs text-gray-500">
                  支持格式: JPG, PNG, MP4, AVI, MOV, MKV (最大 500MB)
                </p>
              </Upload.Dragger>

              {uploadedFile && (
                <Alert
                  message={`已上传: ${uploadedFile.name}`}
                  type="success"
                  showIcon
                  className="mt-3"
                />
              )}

              {fileMetadata && (
                <div className="mt-4 p-3 bg-blue-50 rounded">
                  <p className="text-sm">
                    <strong>视频信息:</strong>
                  </p>
                  <p className="text-sm">帧率: {fileMetadata.fps.toFixed(2)} FPS</p>
                  <p className="text-sm">总帧数: {fileMetadata.frame_count}</p>
                  <p className="text-sm">时长: {fileMetadata.duration_sec.toFixed(2)}秒</p>
                </div>
              )}
            </div>

            <Divider />

            {/* Model Selection */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">2. 选择模型 (Select Model)</h3>
              <Select
                value={selectedModel}
                onChange={setSelectedModel}
                style={{ width: '100%' }}
                placeholder="选择要使用的检测模型"
              >
                {models.map((model) => (
                  <Select.Option key={model.path} value={model.path}>
                    {model.name} ({model.path})
                  </Select.Option>
                ))}
              </Select>
            </div>

            <Divider />

            {/* Detection Options */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">3. 检测选项 (Options)</h3>

              <div className="space-y-4">
                <Checkbox
                  checked={useFilterPerson}
                  onChange={(e) => setUseFilterPerson(e.target.checked)}
                >
                  启用无人帧筛除 (Enable person-less frame filtering)
                </Checkbox>

                <Checkbox
                  checked={useFilterStatic}
                  onChange={(e) => setUseFilterStatic(e.target.checked)}
                >
                  启用静态帧筛除 (Enable static frame filtering)
                </Checkbox>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    每几帧检测一次 (Frame interval for detection)
                  </label>
                  <InputNumber
                    min={1}
                    max={30}
                    value={frameInterval}
                    onChange={(value) => setFrameInterval(value || 1)}
                    style={{ width: '100%' }}
                  />
                  <p className="text-xs text-gray-500 mt-1">推荐设置为 2，以提升效率 (Recommended: 2)</p>
                </div>
              </div>
            </div>

            <Divider />

            {/* Action Buttons */}
            <div>
              <h3 className="text-lg font-semibold mb-3">4. 执行操作 (Actions)</h3>
              <Space className="w-full" style={{ display: 'flex', gap: '8px' }}>
                <Button
                  type="primary"
                  size="large"
                  icon={<PlayCircleOutlined />}
                  onClick={handleDetect}
                  loading={detecting}
                  disabled={!uploadedFile || !selectedModel || uploading}
                  style={{ flex: 1 }}
                >
                  开始检测 (Start Detection)
                </Button>

                {detectionResult && (
                  <Button
                    type="default"
                    size="large"
                    icon={<DownloadOutlined />}
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = detectionResult.downloadUrl;
                      link.download = detectionResult.resultPath.split('/').pop();
                      link.click();
                    }}
                  >
                    下载结果
                  </Button>
                )}

                <Button
                  danger
                  size="large"
                  icon={<ClearOutlined />}
                  onClick={handleClear}
                >
                  清除
                </Button>
              </Space>
            </div>
          </Card>
        </Col>

        {/* Logs Panel */}
        <Col xs={24} lg={8}>
          <Card
            title="检测日志 (Detection Logs)"
            className="shadow-lg h-full"
            headStyle={{ background: '#1890ff', color: 'white' }}
          >
            {detecting && <Spin />}
            <LogPanel logs={logs} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
