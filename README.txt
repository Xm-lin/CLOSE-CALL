遊戲：純靜態 HTML / CSS / JavaScript，可放 GitHub Pages。

上傳
1. 將本資料夾內容上傳到 GitHub 儲存庫，index.html 放在發布目錄根目錄。
2. 啟用 GitHub Pages。遊戲不需要 Python 伺服器。
3. map 資料夾內的 5 張 .txt 都要上傳，另保留 maps.js、map.config.js。

選圖與匯入
- 開始、暫停或結束畫面都能選地圖。換圖會重新開始。
- 「匯入座標檔」可選取一個或多個 txt/json，名稱使用檔名。
- 匯入檔只在目前頁面使用，不會自動上傳 GitHub；重新整理後請再匯入。
- 右上角「如何匯入地圖」有簡短說明。
- 一般 github.io 網址會自動辨識公開儲存庫，透過 GitHub API 列出 map/*.txt。
- 新增 txt 到 map 並完成 Pages 更新後，按「重新讀取」。
- API 額度或網路受限時，使用 maps.js 備份清單；仍會讀取網站的 txt。
- 自訂網域、docs 目錄或非預設分支：在 map.config.js 填寫 owner、repo、branch、path。
- 直接雙擊 index.html 也能玩 5 張離線備份地圖，亦可匯入座標檔。

新增地圖的備份清單
不用啟動任何伺服器。在自己的電腦執行：
  python draw.py --update-list
再上傳 maps.js 和 map/*.txt。draw.py 畫圖時也會順便更新 maps.js。

座標格式
使用 JSON 陣列：
[[0,0],[0,-1500],[2200,-1500],[2200,0]]
或每行 x,y。至少 4 點，最後自動接回第一點。
請避免相鄰重複點、原路直接折返、道路交叉或相距太近。

Python 畫圖（只供作者在電腦畫圖，與網站執行無關）
安裝：python -m pip install -r requirements.txt
選地圖：python draw.py
指定：python draw.py "map/03_蛇行山道.txt"
全部輸出：python draw.py --all --output plots --no-show
圖上直接顯示座標：python draw.py "map/03_蛇行山道.txt" --labels coords
預設圖上只放避讓編號，完整座標列在右側，不會互相擠在一起。
滑鼠移到點附近也能查看完整座標；標籤太密而無空位時，以右側表格與滑鼠提示為準。

單圈計時與操作
W／↑ 加速；S／↓ 減速；A D／← → 轉向；R 立即重新開始目前地圖。
手機按住左右轉向與加速／減速鍵，可同時按。
起步速度為 0，按開始立即計時；跑完一整圈後顯示本圈與最佳時間。
撞牆會減速並留在路內，不會死亡或中斷計時。
鬆開油門會滑行，不倒車。空白／P／Esc 可暫停，切換視窗也會自動暫停。
每張地圖獨立儲存最佳單圈時間；舊版分數不沿用。

可調參數（index.html）
DRIVE.maxSpeed = 610：速度上限
DRIVE.acceleration = 300：加速度
DRIVE.braking = 420：煞車力
DRIVE.coastDrag = 18：滑行減速
甩尾 3.0 秒，收尾 0.65 秒；道路半寬 80，彎角半徑 175。
