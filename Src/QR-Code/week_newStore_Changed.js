const fs = require('fs');
const path = require('path');

// 定義檔案路徑
const earlierDateFilePath = path.join(__dirname, 'search_callMe_earlier_date.json');
const latestDateFilePath = path.join(__dirname, 'search_callMe_latest_date.json');
const sourceFilePath = path.join(__dirname, 'shop_data.json'); // 同目錄下
const newEarlierDateFilePath = earlierDateFilePath; // 重新命名的檔案路徑
const newLatestDateFilePath = latestDateFilePath; // 使用已定義的最新日期檔案路徑



// 1. 刪除 "search_callMe_earlier_date.json" 檔案
fs.unlink(earlierDateFilePath, (err) => {
  if (err) {
    console.error('刪除檔案時發生錯誤:', err);
    return;
  }
  console.log('\n已刪除上上週舊資料檔案:', earlierDateFilePath);

  // 2. 將 "search_callMe_latest_date.json" 檔案變更為 "search_callMe_earlier_date.json"
  fs.rename(latestDateFilePath, newEarlierDateFilePath, (err) => {
    if (err) {
      console.error('變更檔案名稱時發生錯誤:', err);
      return;
    }
    console.log('已將上週最新檔案變更為本週舊檔案:', newEarlierDateFilePath);

    // 3. 將 "shop_data.json" 檔案變更為 "search_callMe_latest_date.json"
    fs.rename(sourceFilePath, newLatestDateFilePath, (err) => {
      if (err) {
        console.error('變更檔案名稱時發生錯誤:', err);
        return;
      }
      console.log('已將拷貝檔案變更為最新檔案:', newLatestDateFilePath);
    });
  });
});