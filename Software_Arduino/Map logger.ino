/*
 * ИДЕАЛЬНЫЙ СИНХРОНИЗАТОР (Гибридный фильтр)
 * 1. Убивает пульсации мотора (аппаратное усреднение за 100мс)
 * 2. Имеет настраиваемые "крутилки" для идеальной гладкости линий.
 */

#include <util/atomic.h>

// ====================================================================
// === НАСТРОЙКИ СГЛАЖИВАНИЯ (КРУТИ ЗДЕСЬ) ============================
// ====================================================================
// Диапазон от 0.01 (очень сильно сглажено, медленно) до 1.0 (без сглаживания, быстро)

const float TUNE_DIFF = 0.2;  // Настройка для графика DIFF (разница)
const float TUNE_MAP  = 0.2;  // Настройка для графиков FRONT MAP и REAR MAP

// ====================================================================


// --- КОНСТАНТЫ КАЛИБРОВКИ ---
const float V2_VOLTAGE_OFFSET = 0.03; // Твое смещение для второго датчика

// Настройки TPS
const float TPS_MIN_VOLTAGE = 0.44;  
const float TPS_MAX_VOLTAGE = 4.05;  

// Характеристики сенсора
const float V_MIN_MV = 516.0;   
const float V_MAX_MV = 4775.0;  
const float P_MIN_KPA = 20.0;  
const float P_MAX_KPA = 100.0; 
const float KPA_TO_INHG = 0.2953;

// Пины
const int pinMap1 = A4; 
const int pinMap2 = A5; 
const int pinTps  = A3; 
const int pinRpm  = 2;  
const float ADC_REF = 5.0; 

// --- ПЕРЕМЕННЫЕ ---
unsigned long sampleCount = 0;
float sumV1 = 0, sumV2 = 0;
float instV1 = 0, instV2 = 0;

// Переменные для финального сглаживания
float finalDiff = 0;
float finalMap1 = 0;
float finalMap2 = 0;
bool firstRun = true;

// RPM
volatile unsigned long lastPulseTime = 0;
volatile unsigned long pulseInterval = 0;
int currentRPM = 0;

// Тайминги
unsigned long startTime = 0;
const unsigned long printInterval = 100; // Вывод каждые 100мс
unsigned long previousMillis = 0;

void rpmInterrupt() {
  unsigned long currentTime = micros();
  pulseInterval = currentTime - lastPulseTime;
  lastPulseTime = currentTime;
}

void setup() {
  Serial.begin(115200);
  pinMode(pinRpm, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(pinRpm), rpmInterrupt, RISING);
  delay(500); 
  startTime = millis();
  
  Serial.println("\"Elapsed Time\",\"FRONT\",\"REAR\",\"DIFF\",\"TPS\",\"RPM\",\"FRONT MAP\",\"REAR MAP\"");
}

void loop() {
  // 1. Быстрый сбор данных (убивает "пилу")
  float v1_raw = analogRead(pinMap1) * (ADC_REF / 1023.0);
  float v2_raw = analogRead(pinMap2) * (ADC_REF / 1023.0);
  
  sumV1 += v1_raw;
  sumV2 += v2_raw;
  sampleCount++;

  instV1 = v1_raw;
  instV2 = v2_raw;

  // 2. Расчет RPM
  unsigned long interval, lastPulse;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { 
    interval = pulseInterval;
    lastPulse = lastPulseTime;
  }
  if (micros() - lastPulse > 1000000) currentRPM = 0; 
  else if (interval > 0) currentRPM = 60000000 / interval; 

  // 3. Вывод и фильтрация раз в 100мс
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= printInterval) {
    previousMillis = currentMillis;

    if (sampleCount == 0) sampleCount = 1;

    // Базовое усреднение за 100мс
    float avgV1 = sumV1 / sampleCount;
    float avgV2 = sumV2 / sampleCount;

    sumV1 = 0; sumV2 = 0; sampleCount = 0;

    float avgV2_calibrated = avgV2 - V2_VOLTAGE_OFFSET;
    float currentDiff = avgV1 - avgV2_calibrated;
    
    float currentMap1 = calcInHg(avgV1);
    float currentMap2 = calcInHg(avgV2_calibrated);

    // НАСТРАИВАЕМАЯ ФИЛЬТРАЦИЯ
    if (firstRun) {
      finalDiff = currentDiff;
      finalMap1 = currentMap1;
      finalMap2 = currentMap2;
      firstRun = false;
    } else {
      // Применяем твои "крутилки"
      finalDiff = (TUNE_DIFF * currentDiff) + ((1.0 - TUNE_DIFF) * finalDiff);
      finalMap1 = (TUNE_MAP * currentMap1) + ((1.0 - TUNE_MAP) * finalMap1);
      finalMap2 = (TUNE_MAP * currentMap2) + ((1.0 - TUNE_MAP) * finalMap2);
    }

    // Очистка нуля
    float outDiff = finalDiff;
    if (abs(outDiff) < 0.005) outDiff = 0.0;

    // TPS
    float tpsV = analogRead(pinTps) * (ADC_REF / 1023.0);
    float tpsPct = (tpsV - TPS_MIN_VOLTAGE) / (TPS_MAX_VOLTAGE - TPS_MIN_VOLTAGE) * 100.0;
    tpsPct = constrain(tpsPct, 0.0, 100.0);

    float timeSec = (currentMillis - startTime) / 1000.0;

    // ВЫВОД В ПОРТ
    Serial.print(timeSec, 3);        Serial.print(",");
    Serial.print(instV1, 2);         Serial.print(","); 
    Serial.print(instV2 - V2_VOLTAGE_OFFSET, 2); Serial.print(","); 
    Serial.print(outDiff, 2);        Serial.print(","); // Настраиваемый DIFF
    Serial.print(tpsPct, 1);         Serial.print(","); 
    Serial.print(currentRPM);        Serial.print(","); 
    Serial.print(finalMap1, 1);      Serial.print(","); // Настраиваемый MAP1
    Serial.println(finalMap2, 1);                       // Настраиваемый MAP2
  }
}

float calcInHg(float voltage) {
  float mv = voltage * 1000.0;
  float kpa = (mv - V_MIN_MV) * (P_MAX_KPA - P_MIN_KPA) / (V_MAX_MV - V_MIN_MV) + P_MIN_KPA;
  kpa = constrain(kpa, P_MIN_KPA, P_MAX_KPA);
  return kpa * KPA_TO_INHG;
}
