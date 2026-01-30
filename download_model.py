from modelscope import snapshot_download

print("开始下载DeepSeek模型...")
print("模型: deepseek-ai/deepseek-llm-7b-chat")
print("使用ModelScope国内镜像，下载速度较快")
print("")

try:
    model_dir = snapshot_download(
        'deepseek-ai/deepseek-llm-7b-chat',
        cache_dir='./models',
        revision='master'
    )
    
    print("")
    print("=" * 60)
    print("模型下载成功！")
    print(f"模型保存路径: {model_dir}")
    print("=" * 60)
    
except Exception as e:
    print("")
    print("=" * 60)
    print(f"模型下载失败: {e}")
    print("=" * 60)
