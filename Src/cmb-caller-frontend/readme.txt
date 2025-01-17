
sudo su
cd cmb-caller-frontend/
screen -mS cmb-caller-frontend python3 cmb-caller-frontend.py



檢查埠佔用情況：

使用以下命令檢查埠 8765 是否被程佔用：
sudo lsof -i :8765

如果有埠被佔用，可以使用以下命令終止佔用：
sudo kill -9 <PID>
