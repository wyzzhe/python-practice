# 提成计算器部署指南

## 方法一：GitHub Pages（免费，推荐）

### 步骤：
1. 在GitHub上创建新仓库
2. 上传 `commission_calculator.html` 文件
3. 在仓库设置中启用GitHub Pages
4. 获得类似 `https://username.github.io/repository-name/commission_calculator.html` 的链接
5. 将链接发送给用户

### 优点：
- 完全免费
- 全球访问速度快
- 支持HTTPS
- 无需服务器维护

## 方法二：Netlify（免费，简单）

### 步骤：
1. 访问 [netlify.com](https://netlify.com)
2. 注册账号
3. 拖拽HTML文件到部署区域
4. 获得类似 `https://random-name.netlify.app` 的链接
5. 将链接发送给用户

### 优点：
- 拖拽即部署
- 自动HTTPS
- 全球CDN
- 支持自定义域名

## 方法三：Vercel（免费，快速）

### 步骤：
1. 访问 [vercel.com](https://vercel.com)
2. 注册账号
3. 导入项目或直接上传HTML文件
4. 获得类似 `https://project-name.vercel.app` 的链接
5. 将链接发送给用户

## 方法四：本地服务器（临时测试）

如果需要快速测试，可以使用Python内置服务器：

```bash
# 在commission_cal目录下运行
python -m http.server 8000
```

然后访问 `http://你的IP地址:8000/commission_calculator.html`

## 推荐方案

**对于非技术用户**：推荐使用 **Netlify**，操作最简单
**对于技术用户**：推荐使用 **GitHub Pages**，更专业
**对于临时使用**：直接发送HTML文件即可
