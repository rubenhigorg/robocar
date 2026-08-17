/*
 * Robocar - firmware del Nano contador de la rueda dentada (v2, alta frecuencia).
 *
 * Cuenta cada pulso por INTERRUPCION (D2 = INT0) y expone por I2C (esclavo 0x08)
 * un CONTADOR ACUMULATIVO de 16 bits (2 bytes, little-endian). La Raspberry lo
 * lee a ~30 Hz y deriva la velocidad como delta_cuenta/delta_t (con manejo de
 * desbordamiento de 16 bits: leyendo rapido, el delta siempre < 65536).
 *
 * Se usan 2 bytes (no 4) a proposito: es el mismo tamano de transaccion que el
 * firmware antiguo, que era fiable con el I2C de la Pi (que tiene problemas con
 * el clock-stretching de esclavos). onRequest es minimo: escribe un buffer ya
 * preparado en loop(), sin deshabilitar interrupciones dentro del ISR del TWI.
 *
 * Encoder: senal en D2 (INT0). I2C: A4=SDA, A5=SCL (esclavo 0x08).
 */
#include <Wire.h>

const uint8_t I2C_ADDR = 0x08;
const uint8_t ENC_PIN  = 2;      // D2 = INT0

volatile uint16_t pulseCount = 0;
volatile uint8_t  snap[2] = {0, 0};

void onPulse() {
  pulseCount++;
}

void requestEvent() {
  Wire.write((uint8_t *)snap, 2);   // rapido: solo el buffer ya armado
}

void receiveEvent(int howMany) {
  while (Wire.available()) Wire.read();   // consume el byte de "registro"
}

void setup() {
  pinMode(ENC_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_PIN), onPulse, RISING);
  Wire.begin(I2C_ADDR);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
}

void loop() {
  noInterrupts();
  uint16_t c = pulseCount;
  interrupts();
  snap[0] = (uint8_t)(c & 0xFF);
  snap[1] = (uint8_t)((c >> 8) & 0xFF);
}
