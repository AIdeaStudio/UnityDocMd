# UnityDocMd
## 自动将unity本地开发文档整理为适合RAG的markdown格式 移除所有无用的文本和元素 仅保留结构清晰的教程文字本身
### 如果直接用原始文档做RAG 会索引、查询大量的无用前端标记 实测会极大干扰检索效果 根本达不到可用的标准
---
*检索效果测试（gemini2.5-flash-lite+qwen3-embedding-4B-Q8'）：*  
### 原始HTML文档
---

<img width="798" height="531" alt="屏幕截图 2025-07-30 034631" src="https://github.com/user-attachments/assets/185feef0-137a-4d98-b46f-7ad02d89a6d5" /> 
<img width="850" height="1014" alt="屏幕截图 2025-07-30 034650" src="https://github.com/user-attachments/assets/9da19b58-598c-4c47-9349-9b7b519ce92d" />

---
### 整理后markdown文档

<img width="782" height="479" alt="屏幕截图 2025-07-30 034424" src="https://github.com/user-attachments/assets/933d897b-5fe7-4d79-903f-6e3a746de203" />
<img width="841" height="975" alt="屏幕截图 2025-07-30 034443" src="https://github.com/user-attachments/assets/37d46916-801a-4e76-90fe-2e5b30853441" />

---
### 整理效果
<img width="2073" height="1189" alt="image" src="https://github.com/user-attachments/assets/b1f2eb78-7d62-4c5b-871f-28e5a0249683" />

<img width="1376" height="926" alt="image" src="https://github.com/user-attachments/assets/1986f160-af50-463e-b220-57b71cd1ae7a" />



## 使用方法
下载unity的同时勾选document  
前往**Unity安装文件夹\6000.1.1f1\Editor\Data\Documentation\en** 拷贝manual和scriptreference文件夹 和脚本放在一起  
然后pip安装
---
beautifulsoup4
markdownify
---
即可直接运行 会自动输出到两个新文件夹内 并保持原有文件夹结构和文件名
