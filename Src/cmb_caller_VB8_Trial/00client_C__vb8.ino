#include <Arduino.h>
#include "ma_Functions.h"

#include "esp_task_wdt.h"

#define BLED 2
///
TaskHandle_t Task1;
TaskHandle_t Task0;
//
unsigned int BLED_Ms = 500;         //500ms
unsigned long BLED_delayStart = 0;  // the time the delay started
byte led_light_en = 0;
//
int a = 0;
int a1 = 1;
//
void BLED_Blinking() {
  if ((millis() - BLED_delayStart) >= BLED_Ms) {
    BLED_delayStart = millis();
    if (led_light_en == 0) {
      digitalWrite(BLED, HIGH);
      led_light_en = 1;
    } else {
      digitalWrite(BLED, LOW);
      led_light_en = 0;
    }
    //
    a1++;
    if (a1 >= 20) {
      bool ok = ma_set_data(a);
      if (ok == true) {
        a++;
        if (a > 999) {
          a = 0;
        }
      }
      a1 = 0;
    }
  }
}

TaskHandle_t Task1l;

//
// void setup()
void setup_x() {
  Serial.begin(115200);
  Serial.setTimeout(200);

  Serial.println("\n\n==================Call Call Me Key" + String(esp32_version) + "  =====================\n");

  //create a task that will be executed in the Task2code() function, with priority 1 and executed on core 1
  xTaskCreatePinnedToCore(
    Task0code, /* Task function. */
    "Task0",   /* name of task. */
    10000,     /* Stack size of task */
    NULL,      /* parameter of the task */
    1,         /* priority of the task */   // OK: 0 , 1
    &Task0,    /* Task handle to keep track of created task */
    // 0);          /* pin task to core 1 */
    1); /* pin task to core 0 */
  delay(500);

  xTaskCreatePinnedToCore(
    Task1code, /* Task function. */
    "Task1",   /* name of task. */
    10000,     /* Stack size of task */
    NULL,      /* parameter of the task */
    1,         /* priority of the task */   // 1 OK?, 與 RF之priority 大於(等於?)可以，(等於?)小於不行.
    &Task1,    /* Task handle to keep track of created task */
    // 1);          /* pin task to core 0 */
    0); /* pin task to core 0 */
  delay(500);

  // xTaskCreatePinnedToCore(
  //   Task1lcode, /* Task function. */
  //   "Task1l",   /* name of task. */
  //   10000,      /* Stack size of task */
  //   NULL,       /* parameter of the task */
  //   5,          /* priority of the task */
  //   &Task1l,    /* Task handle to keep track of created task */
  //   0);         /* pin task to core 0 */
  // delay(500);



  // 建立 watchdog 設定結構
  // esp_task_wdt_config_t wdt_config = {
  //   .timeout_ms = 90000,   // 設定 timeout 為 10 秒
  //   .trigger_panic = true  // 超時時觸發 panic（可選）
  // };

  // // 初始化 watchdog
  // esp_task_wdt_init(&wdt_config);
  // esp_task_wdt_add(NULL);  // 將目前任務加入 Watchdog 監控

  Serial.print("\n**********Setup Done.**********\n");
}


void Task1code(void* pvParameters) {
  Serial.print("[CFG] Task1 RF core ");
  Serial.println(xPortGetCoreID());

  // esp_task_wdt_delete(NULL);  // 移除目前任務的 WDT 監控

  ma_set();
}

void Task1lcode(void* pvParameters) {
  Serial.print("[CFG] Task1l loop RF core ");
  Serial.println(xPortGetCoreID());
  while (1) {
    Serial.print(" LC0");
    delay(10000);
  }
}

void Task0code(void* pvParameters) {
  Serial.print("[CFG] Task0 core ");
  Serial.println(xPortGetCoreID());

  pinMode(BLED, OUTPUT);
  while (1) {
    BLED_Blinking();
    // delay(1);//ms 一定要有 watch dog 用
    delay(0);  //ms 一定要有 watch dog 用
  }
}

// void loop()
// {
//   int b=ma_get_data();
//   if (b>=0)//-1 沒收到值
//   {
//     String ss= "[MSG] rev data " + String (b);
//     Serial.println(ss);
//   }
//   delay(100);
//   //程式

// }
