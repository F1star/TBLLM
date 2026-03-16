<template>
  <div class="file-upload-container">
    <h3>文件上传</h3>
    
    <div class="upload-section">
      <input 
        type="file" 
        id="fileInput" 
        ref="fileInputRef" 
        @change="handleFileChange" 
        accept=".pdf,.docx,.txt"
        class="file-input"
      />
      <label for="fileInput" class="upload-btn">
        <span class="btn-icon">📁</span>
        <span class="btn-text">{{ selectedFile ? selectedFile.name : '选择文件' }}</span>
      </label>
      <button @click="uploadFile" :disabled="!selectedFile || isUploading" class="submit-btn">
        <span v-if="!isUploading">上传文件</span>
        <span v-else>上传中...</span>
      </button>
    </div>
    
    <div v-if="uploadResult" class="upload-result">
      <h4>解析结果</h4>
      <div class="result-item">
        <span class="label">文件名:</span>
        <span class="value">{{ uploadResult.filename }}</span>
      </div>
      <div class="result-item">
        <span class="label">上传时间:</span>
        <span class="value">{{ new Date(uploadResult.upload_time).toLocaleString('zh-CN') }}</span>
      </div>
      <div class="result-item">
        <span class="label">解析内容:</span>
        <div class="content-preview">{{ uploadResult.parsed_text }}</div>
      </div>
    </div>
    
    <div v-if="userFiles.length > 0" class="files-list">
      <h4>已上传文件</h4>
      <div class="files-grid">
        <div v-for="file in userFiles" :key="file.id" class="file-card">
          <div class="file-icon" :class="getFileType(file.filename)">
            {{ getFileIcon(file.filename) }}
          </div>
          <div class="file-info">
            <div class="file-name">{{ file.filename }}</div>
            <div class="file-time">{{ new Date(file.upload_time).toLocaleString('zh-CN') }}</div>
          </div>
          <div class="file-actions">
            <button @click="viewFileContent(file.id)" class="action-btn view-btn">
              查看
            </button>
            <button @click="downloadFile(file.id, file.filename)" class="action-btn download-btn">
              下载
            </button>
            <button @click="deleteFile(file.id)" class="action-btn delete-btn">
              删除
            </button>
            <button @click="useFileForEvaluation(file.id)" class="action-btn eval-btn">
              评估
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="fileContent" class="file-content-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h4>{{ fileContent.filename }}</h4>
          <button @click="fileContent = null" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <pre>{{ fileContent.content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FileUpload',
  data() {
    return {
      selectedFile: null,
      isUploading: false,
      uploadResult: null,
      userFiles: [],
      fileContent: null
    };
  },
  mounted() {
    this.loadUserFiles();
  },
  methods: {
    handleFileChange(e) {
      this.selectedFile = e.target.files[0];
    },
    async uploadFile() {
      if (!this.selectedFile) return;
      
      this.isUploading = true;
      const formData = new FormData();
      formData.append('file', this.selectedFile);
      
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5000/api/files/upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });
        
        if (response.ok) {
          const data = await response.json();
          this.uploadResult = data;
          this.loadUserFiles();
          this.$refs.fileInputRef.value = '';
          this.selectedFile = null;
        } else {
          const error = await response.json();
          alert('上传失败: ' + (error.error || '未知错误'));
        }
      } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败，请稍后重试');
      } finally {
        this.isUploading = false;
      }
    },
    async loadUserFiles() {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5000/api/files', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          this.userFiles = await response.json();
        }
      } catch (error) {
        console.error('获取文件列表失败:', error);
      }
    },
    async viewFileContent(fileId) {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:5000/api/files/${fileId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          this.fileContent = await response.json();
        }
      } catch (error) {
        console.error('获取文件内容失败:', error);
      }
    },
    useFileForEvaluation(fileId) {
      // 触发父组件的评估事件，传递文件ID
      this.$emit('useForEvaluation', fileId);
    },
    async downloadFile(fileId, filename) {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:5000/api/files/${fileId}/download`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        } else {
          const error = await response.json();
          alert('下载失败: ' + (error.error || '未知错误'));
        }
      } catch (error) {
        console.error('下载失败:', error);
        alert('下载失败，请稍后重试');
      }
    },
    async deleteFile(fileId) {
      if (!confirm('确定要删除这个文件吗？')) {
        return;
      }
      
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:5000/api/files/${fileId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          alert('文件删除成功');
          this.loadUserFiles();
        } else {
          const error = await response.json();
          alert('删除失败: ' + (error.error || '未知错误'));
        }
      } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请稍后重试');
      }
    },
    getFileIcon(filename) {
      const ext = filename.split('.').pop().toLowerCase();
      if (ext === 'pdf') return '📄';
      if (ext === 'docx') return '📃';
      if (ext === 'txt') return '📝';
      return '📄';
    },
    getFileType(filename) {
      const ext = filename.split('.').pop().toLowerCase();
      if (ext === 'pdf') return 'pdf';
      if (ext === 'docx') return 'docx';
      if (ext === 'txt') return 'txt';
      return 'other';
    }
  }
};
</script>

<style scoped>
.file-upload-container {
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h3 {
  margin-bottom: 20px;
  color: #1e293b;
  font-size: 1.2rem;
  font-weight: 600;
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.file-input {
  display: none;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #f1f5f9;
  border: 2px dashed #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 200px;
  justify-content: center;
}

.upload-btn:hover {
  border-color: #64748b;
  background: #e2e8f0;
}

.btn-icon {
  font-size: 1.2rem;
}

.btn-text {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.submit-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-result {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.upload-result h4 {
  margin-bottom: 15px;
  color: #1e293b;
  font-size: 1rem;
  font-weight: 600;
}

.result-item {
  display: flex;
  margin-bottom: 10px;
  align-items: flex-start;
}

.result-item .label {
  font-weight: 600;
  color: #64748b;
  min-width: 80px;
}

.result-item .value {
  color: #334155;
  flex: 1;
}

.content-preview {
  background: #f8fafc;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  max-height: 200px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.5;
  color: #475569;
}

.files-list {
  margin-top: 30px;
}

.files-list h4 {
  margin-bottom: 15px;
  color: #1e293b;
  font-size: 1rem;
  font-weight: 600;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.file-card {
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
}

.file-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.file-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.file-icon.pdf {
  background: #fef2f2;
  color: #ef4444;
}

.file-icon.docx {
  background: #eff6ff;
  color: #3b82f6;
}

.file-icon.txt {
  background: #fefce8;
  color: #f59e0b;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-time {
  font-size: 12px;
  color: #94a3b8;
}

.file-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-btn {
  background: #f1f5f9;
  color: #64748b;
}

.view-btn:hover {
  background: #e2e8f0;
}

.eval-btn {
  background: #dcfce7;
  color: #16a34a;
}

.eval-btn:hover {
  background: #bbf7d0;
}

.download-btn {
  background: #dbeafe;
  color: #3b82f6;
}

.download-btn:hover {
  background: #bfdbfe;
}

.delete-btn {
  background: #fee2e2;
  color: #ef4444;
}

.delete-btn:hover {
  background: #fecaca;
}

.file-content-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.modal-header h4 {
  margin: 0;
  color: #1e293b;
  font-size: 1.1rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.close-btn:hover {
  background: #e2e8f0;
}

.modal-body {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

.modal-body pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #334155;
  white-space: pre-wrap;
  word-wrap: break-word;
}

@media (max-width: 768px) {
  .upload-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .upload-btn {
    min-width: auto;
  }
  
  .files-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    width: 95%;
  }
}
</style>
