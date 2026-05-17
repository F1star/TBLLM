<template>
  <div class="file-upload-container">
    <!-- Upload area -->
    <div class="upload-area">
      <div class="upload-section">
        <input type="file" id="fileInput" ref="fileInputRef" @change="handleFileChange" accept=".pdf,.docx,.txt" class="file-input" />
        <label for="fileInput" class="upload-btn" :class="{ 'has-file': selectedFile }">
          <svg v-if="!selectedFile" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
          </svg>
          <span class="btn-text">{{ selectedFile ? selectedFile.name : '选择文件' }}</span>
        </label>
        <button @click="uploadFile" :disabled="!selectedFile || isUploading" class="submit-btn">
          <span v-if="!isUploading">上传</span>
          <span v-else class="uploading-text">上传中<span class="dots"><span>.</span><span>.</span><span>.</span></span></span>
        </button>
      </div>
      <p class="upload-hint">支持 PDF、DOCX、TXT 格式</p>
    </div>

    <!-- Upload result -->
    <div v-if="uploadResult" class="upload-result">
      <div class="result-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <span>解析完成</span>
      </div>
      <div class="result-item">
        <span class="result-label">文件名</span>
        <span class="result-value">{{ uploadResult.filename }}</span>
      </div>
      <div class="result-item">
        <span class="result-label">上传时间</span>
        <span class="result-value">{{ new Date(uploadResult.upload_time).toLocaleString('zh-CN') }}</span>
      </div>
      <div class="result-item content-preview">
        <span class="result-label">解析内容</span>
        <div class="preview-text">{{ uploadResult.parsed_text }}</div>
      </div>
    </div>

    <!-- Files list -->
    <div v-if="userFiles.length > 0" class="files-section">
      <div class="files-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <span>已上传文件</span>
      </div>
      <div class="files-grid">
        <div v-for="file in userFiles" :key="file.id" class="file-card">
          <div class="file-icon" :class="getFileType(file.filename)">
            <svg v-if="getFileType(file.filename) === 'pdf'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            <svg v-else-if="getFileType(file.filename) === 'docx'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          </div>
          <div class="file-info">
            <div class="file-name">{{ file.filename }}</div>
            <div class="file-time">{{ new Date(file.upload_time).toLocaleString('zh-CN') }}</div>
          </div>
          <div class="file-actions">
            <button @click="viewFileContent(file.id)" class="file-action-btn view" title="查看">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button @click="downloadFile(file.id, file.filename)" class="file-action-btn download" title="下载">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
            <button @click="useFileForEvaluation(file.id)" class="file-action-btn evaluate" title="评估">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            </button>
            <button @click="deleteFile(file.id)" class="file-action-btn delete" title="删除">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Content Modal -->
    <div v-if="fileContent" class="modal-overlay" @click.self="fileContent = null">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ fileContent.filename }}</h3>
          <button @click="fileContent = null" class="close-btn">&times;</button>
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
    return { selectedFile: null, isUploading: false, uploadResult: null, userFiles: [], fileContent: null };
  },
  mounted() { this.loadUserFiles(); },
  methods: {
    handleFileChange(e) { this.selectedFile = e.target.files[0]; },
    async uploadFile() {
      if (!this.selectedFile) return;
      this.isUploading = true;
      const fd = new FormData();
      fd.append('file', this.selectedFile);
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5050/api/files/upload', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: fd
        });
        if (res.ok) {
          this.uploadResult = await res.json();
          this.loadUserFiles();
          this.$refs.fileInputRef.value = '';
          this.selectedFile = null;
        } else {
          const e = await res.json();
          alert('上传失败: ' + (e.error || '未知错误'));
        }
      } catch (e) { console.error(e); alert('上传失败'); }
      finally { this.isUploading = false; }
    },
    async loadUserFiles() {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5050/api/files', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) this.userFiles = await res.json();
      } catch (e) { console.error(e); }
    },
    async viewFileContent(id) {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`http://localhost:5050/api/files/${id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) this.fileContent = await res.json();
      } catch (e) { console.error(e); }
    },
    useFileForEvaluation(id) { this.$emit('useForEvaluation', id); },
    async downloadFile(id, filename) {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`http://localhost:5050/api/files/${id}/download`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = filename;
          document.body.appendChild(a); a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }
      } catch (e) { alert('下载失败'); }
    },
    async deleteFile(id) {
      if (!confirm('确定要删除这个文件吗？')) return;
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`http://localhost:5050/api/files/${id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) { alert('删除成功'); this.loadUserFiles(); }
        else { const e = await res.json(); alert('删除失败: ' + (e.error || '')); }
      } catch (e) { alert('删除失败'); }
    },
    getFileType(filename) {
      const ext = filename.split('.').pop().toLowerCase();
      if (ext === 'pdf') return 'pdf';
      if (ext === 'docx') return 'docx';
      return 'txt';
    }
  }
};
</script>

<style scoped>
.file-upload-container { padding: 0; }

.upload-area {
  padding: 32px;
  margin-bottom: 24px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  text-align: center;
}

.upload-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.file-input { display: none; }

.upload-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  background: rgba(255,255,255,0.03);
  border: 1px dashed rgba(255,255,255,0.12);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 220px;
  justify-content: center;
  color: #5a6275;
}

.upload-btn:hover {
  border-color: rgba(0,229,255,0.25);
  background: rgba(0,229,255,0.03);
  color: #00e5ff;
}

.upload-btn.has-file {
  border-color: rgba(0,229,255,0.2);
  background: rgba(0,229,255,0.04);
  color: #00e5ff;
  border-style: solid;
}

.btn-text {
  font-size: 13px;
  font-weight: 500;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.submit-btn {
  padding: 14px 28px;
  background: linear-gradient(135deg, rgba(0,229,255,0.1), rgba(124,77,255,0.1));
  border: 1px solid rgba(0,229,255,0.2);
  border-radius: 10px;
  color: #00e5ff;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0,229,255,0.18), rgba(124,77,255,0.18));
  box-shadow: 0 0 24px rgba(0,229,255,0.08);
}

.submit-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.uploading-text { display: inline-flex; align-items: center; gap: 2px; }
.dots span { animation: dotPulse 1.4s infinite; }
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }

.upload-hint {
  font-size: 11px;
  color: #5a6275;
  margin-top: 12px;
}

.upload-result {
  padding: 20px;
  margin-bottom: 24px;
  background: rgba(0,230,118,0.03);
  border: 1px solid rgba(0,230,118,0.1);
  border-radius: 12px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #00e676;
  margin-bottom: 16px;
}

.result-item {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
  align-items: flex-start;
}

.result-label {
  color: #5a6275;
  min-width: 80px;
  flex-shrink: 0;
}

.result-value {
  color: #8892a4;
  word-break: break-all;
}

.content-preview { flex-direction: column; }

.preview-text {
  font-size: 12px;
  color: #5a6275;
  line-height: 1.6;
  max-height: 100px;
  overflow-y: auto;
  padding: 10px;
  background: rgba(255,255,255,0.02);
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.06);
}

.files-section {
  margin-top: 24px;
}

.files-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #8892a4;
  margin-bottom: 16px;
}

.files-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }

.file-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  transition: all 0.3s;
}

.file-card:hover {
  background: rgba(255,255,255,0.03);
  border-color: rgba(0,229,255,0.1);
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-icon.pdf { background: rgba(255,23,68,0.1); color: #ff1744; }
.file-icon.docx { background: rgba(68,138,255,0.1); color: #448aff; }
.file-icon.txt { background: rgba(255,171,0,0.1); color: #ffab00; }

.file-info { flex: 1; min-width: 0; }

.file-name {
  font-size: 13px;
  color: #e8eaed;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.file-time { font-size: 11px; color: #5a6275; }

.file-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.file-action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  background: rgba(255,255,255,0.03);
  color: #5a6275;
}

.file-action-btn:hover { background: rgba(255,255,255,0.06); color: #8892a4; }
.file-action-btn.view:hover { color: #00e5ff; background: rgba(0,229,255,0.08); }
.file-action-btn.download:hover { color: #448aff; background: rgba(68,138,255,0.08); }
.file-action-btn.evaluate:hover { color: #00e676; background: rgba(0,230,118,0.08); }
.file-action-btn.delete:hover { color: #ff1744; background: rgba(255,23,68,0.08); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}

.modal {
  background: rgba(13,20,33,0.96);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0,229,255,0.1);
  border-radius: 14px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.modal-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: #e8eaed;
  letter-spacing: 0.5px;
}

.close-btn {
  background: none; border: none;
  color: #5a6275; font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: 60vh;
}

.modal-body pre {
  margin: 0;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  line-height: 1.6;
  color: #8892a4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.preview-text::-webkit-scrollbar { width: 4px; }
.preview-text::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.1); border-radius: 2px; }

@media (max-width: 768px) {
  .upload-section { flex-direction: column; align-items: stretch; }
  .upload-btn { min-width: auto; }
  .files-grid { grid-template-columns: 1fr; }
}
</style>
