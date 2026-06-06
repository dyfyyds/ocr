# ============================================================
#  前端 Dockerfile - Nginx 托管静态原型文件
# ============================================================
FROM nginx:alpine

# 复制原型文件到 nginx 默认静态目录
COPY index.html /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY space_bg.png /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
