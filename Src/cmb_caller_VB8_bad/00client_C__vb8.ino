#include <Arduino.h>
#include "ma_Functions.h"

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

void setup_VB8();
//
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(200);

  // setup_VB8(); // ?????

  Serial.println("\n\n==================Call Call Me Key" + String(esp32_version) + "  =====================\n");

  xTaskCreatePinnedToCore(
    Task1code, /* Task function. */
    "Task1",   /* name of task. */
    10000,     /* Stack size of task */
    NULL,      /* parameter of the task */
    1,         /* priority of the task */
    &Task1,    /* Task handle to keep track of created task */
    1);        /* pin task to core 0 */
  delay(500);

  //create a task that will be executed in the Task2code() function, with priority 1 and executed on core 1
  xTaskCreatePinnedToCore(
    Task0code, /* Task function. */
    "Task0",   /* name of task. */
    10000,     /* Stack size of task */
    NULL,      /* parameter of the task */
    0,         /* priority of the task */
    &Task0,    /* Task handle to keep track of created task */
    0);        /* pin task to core 1 */
  delay(500);

  Serial.print("\n**********Setup Done.**********\n");

}

void Task1code(void* pvParameters) {
  Serial.print("[CFG] Task1 RF core ");
  Serial.println(xPortGetCoreID());

  ma_set();
}

void loop_VB8();

void Task0code(void* pvParameters) {
  Serial.print("[CFG] Task0 core ");
  Serial.println(xPortGetCoreID());

  pinMode(BLED, OUTPUT);
  while (1) {
    // loop_VB8();
    BLED_Blinking();
    delay(1);  //ms 一定要有 watch dog 用
  }
}

void loop() {
  // int b = ma_get_data();
  // if (b >= 0)  //-1 沒收到值
  // {
  //   String ss = "[MSG] rev data " + String(b);
  //   Serial.println(ss);
  // }
  // delay(100);
  // //程式
}
