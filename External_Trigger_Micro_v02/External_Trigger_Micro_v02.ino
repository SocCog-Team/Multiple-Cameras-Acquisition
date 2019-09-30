/*External Trigger Code to be used with AcquisitionTest.py and Adafruit Feather M0 board with trigger input connected to Pin 6
  Pin 5 can be connected to LED to see if trigger pulse is active and o check synchronisation
  Camera GPIO operateds on 3.3V so do not use this with Arduino UNO (5V Logic might damage Cameras)

  The idea is to drive three output pins and the LED on pin13 with different multiples of a common base frequency
  to avoid divisions we use integer multiples of a base period to get the slower versions

  All output triggers are gated by the input pin (1) being HIGH.

  TODO:
  check micros() wrap around
  There are two issues:
  1) start/stop times for specific outputs might be wrapped around and hence << current_time_us
  2) start/stop times for specific outputs might be close to maxiumum, but current_time_us already wrapped around

*/

uint32_t count = 0;

uint32_t current_time_us = 0;
uint32_t last_time_us = 0;
uint32_t base_pulse_count = 0;
uint32_t next_base_pulse_start_ts = 0;
uint32_t base_pulse_start_ts = 0;
uint32_t loop_start_ts_us = 0;

// to make sure the pulse trains are synchronized they are all based on the same
//  base frequency (better are integer multiples of a common base period)
uint32_t base_period_us = 10 * 1000;  // this is 10ms or 100Hz


// the OUTPUT pins
int output_pin_lists[] = {5, 6, 9, LED_BUILTIN}; // LED_BUILTIN (pin13) is a LED
int LED_period_multiplier = 100;
int output_period_multiplier_list[] = {1, 2, 4, LED_period_multiplier};
int LED_pulse_dur_ms = ((base_period_us * LED_period_multiplier) / 1000) * 0.5;
int output_pulse_width_ms_list[] = {4, 18, 36, LED_pulse_dur_ms};
int output_pin_state_list[] = {LOW, LOW, LOW, LOW};

uint32_t output_pulse_start_ts_list[] = {0, 0, 0, 0};
uint32_t output_pulse_stop_ts_list[] = {0, 0, 0, 0};

// how many entries in the output list
int num_output_pins = (sizeof(output_pin_lists) / sizeof(output_pin_lists[0]));


// the input pins:
int input_pin = 1;
int input_pin_state = LOW;
int output_on_input_state = HIGH; // outputs are only active during this input state
int input_pin_last_state = input_pin_state;

void setup() {
  // configure the output lines/pins
  for (byte i_pin = 0; i_pin < num_output_pins; i_pin++) {
    pinMode(output_pin_lists[i_pin], OUTPUT);
  }

  // configure inputs
  // TODO trigger line for stopping the output?
  pinMode(input_pin, INPUT_PULLUP);

  //attachInterrupt(digitalPinToInterrupt(12), trigger_detected, RISING);
  Serial.begin(115200);
  // trigger execution by serial input
  //while (!Serial.available());
}


void loop() {
  // TODO allow more elaborate configuration strings
  // get new base_period_us from serial port
  if (Serial.available())  {
    base_period_us = Serial.read();
    Serial.println(base_period_us);
    // reset base_pulse_count to start fresh
    base_pulse_count = 0;
  }


  // get the current time
  current_time_us = micros();
  // detect overflow/wrap-around
  if (last_time_us > current_time_us) {
    // TODO fix wrap around???
  }

  input_pin_state = digitalRead(input_pin);
  if (input_pin_state == output_on_input_state) {

    if (input_pin_last_state != input_pin_state) {
      // reset base_pulse_count to start fresh, so output pulses are aligned to the input line's activity
      // this is relative costly... but hopefully also rare.
      base_pulse_count = 0;
    }

    // initialize/reset stuff
    if (base_pulse_count == 0) {
      loop_start_ts_us = current_time_us; // the reference time to base all timing on
      base_pulse_start_ts = loop_start_ts_us;

      for (byte i_pin = 0; i_pin < num_output_pins; i_pin++) {
        output_pulse_start_ts_list[i_pin] = current_time_us;
        output_pulse_stop_ts_list[i_pin] = current_time_us + (1000 * output_pulse_width_ms_list[i_pin]);
        digitalWrite(output_pin_lists[i_pin], LOW);
        output_pin_state_list[i_pin] = LOW;
      }

    }

    // base cycle (all pulse start points are entrained to this)
    if (base_pulse_start_ts <= current_time_us) {
      base_pulse_count++;
      base_pulse_start_ts = loop_start_ts_us + (base_pulse_count * base_period_us); // the next base pulse start time

      // we just atrted a base period so check which pins to pull HIGH (pull all high on the first)
      for (byte i_pin = 0; i_pin < num_output_pins; i_pin++) {
        // which pins need to be started
        if ((output_pin_state_list[i_pin] == LOW) && (output_pulse_start_ts_list[i_pin] <= current_time_us)) {
          digitalWrite(output_pin_lists[i_pin], HIGH);
          output_pulse_stop_ts_list[i_pin] = micros() + (1000 * output_pulse_width_ms_list[i_pin]); // get the best estimate for pulse end time stamp
          output_pin_state_list[i_pin] = HIGH;  // mark as high
          // when to start the next pulse
          output_pulse_start_ts_list[i_pin] = loop_start_ts_us + ((base_pulse_count - 1) * base_period_us) + (output_period_multiplier_list[i_pin] * base_period_us);
        }
      }
    }

    // check which pins to pull LOW (this is basically asynchronous from the start timestamps as pulse width are variable)
    for (byte i_pin = 0; i_pin < num_output_pins; i_pin++) {
      // which pins need to be stopped
      if ((output_pin_state_list[i_pin] == HIGH) && (output_pulse_stop_ts_list[i_pin] <= current_time_us)) {
        digitalWrite(output_pin_lists[i_pin], LOW);
        output_pulse_stop_ts_list[i_pin] = 0;
        output_pin_state_list[i_pin] = LOW;  // mark as low
      }
    }
    input_pin_last_state = input_pin_state;
  }
  last_time_us = current_time_us;
}
