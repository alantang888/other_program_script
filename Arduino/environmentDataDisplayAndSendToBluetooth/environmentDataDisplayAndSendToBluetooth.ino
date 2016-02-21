#include <aJSON.h>
#include <SoftwareSerial.h>
#include "DHT.h"
#include <Wire.h>
#include "Adafruit_BMP085.h"

#define GET_DATA_INTERVAL 2000
#define SEND_DATA_INTERVAL 10000
#define BLUETOOTH_TX_PIN 2
#define BLUETOOTH_RX_PIN 3
#define DHT22_PIN 4
#define UNSIGNED_LONG_MAX 4294967295

#define PIN_A 5
#define PIN_B 6
#define PIN_C 7
#define PIN_D 8
#define PIN_E 9
#define PIN_F 10
#define PIN_G 11
#define PIN_H 12

#define PIN_DIGI1  14
#define PIN_DIGI2  15
#define PIN_DIGI3  16
#define PIN_DIGI4  17

#define RELAY_PIN 13
#define RELAY_ON HIGH
#define RELAY_OFF LOW
#define RELAY_TRIGGER_ON 21.5 //Lower than this will trigger on
#define RELAY_TRIGGER_OFF 22.5 //higher than this will trigger off

#define RELAY_CONTROL_TEMPERATURE_DIFFERENT 0.4

#define DELAY_VALUE 55

DHT dht;

// for control read data and send data
unsigned long lastGetData;
unsigned long lastSendData;
unsigned long currentTime;

// for store data
float humidity;
float dhtTemperature;
float bmpTemperature;
long pressure;

bool showTemperature;

// for relay control
float relayTiggerOn;
float relayTiggerOff;

// for remote relay control
int serialNumber;

// for read data
char readBuffer[128];
char temp;
int i = 0;

SoftwareSerial mySerial(BLUETOOTH_RX_PIN, BLUETOOTH_TX_PIN);

Adafruit_BMP085 bmp;

void clearLED()
{
	int i;
	for(i = PIN_A; i <= PIN_H; i++)
	{
		digitalWrite(i, LOW);
	}
}

void pickDigit(int digit)
{
	int i;
	for(i=PIN_DIGI1; i<=PIN_DIGI4;i++)
	{
		digitalWrite(i, HIGH);
	}

	digitalWrite(PIN_DIGI1+(digit-1), LOW);
}

void display1()
{
	digitalWrite(PIN_A, LOW);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, LOW);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, LOW);
	digitalWrite(PIN_G, LOW);
	digitalWrite(PIN_H, LOW);
}

void display2()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, LOW);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, HIGH);
	digitalWrite(PIN_F, LOW);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void display3()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, LOW);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void display4()
{
	digitalWrite(PIN_A, LOW);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, LOW);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void display5()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, LOW);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void display6()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, LOW);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, HIGH);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void display7()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, LOW);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, LOW);
	digitalWrite(PIN_G, LOW);
	digitalWrite(PIN_H, LOW);
}

void display8()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, HIGH);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void display9()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void display0()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, HIGH);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, LOW);
	digitalWrite(PIN_H, LOW);
}

void displayDot()
{
	digitalWrite(PIN_A, LOW);
	digitalWrite(PIN_B, LOW);
	digitalWrite(PIN_C, LOW);
	digitalWrite(PIN_D, LOW);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, LOW);
	digitalWrite(PIN_G, LOW);
	digitalWrite(PIN_H, HIGH);
}

void displayC()
{
	digitalWrite(PIN_A, HIGH);
	digitalWrite(PIN_B, LOW);
	digitalWrite(PIN_C, LOW);
	digitalWrite(PIN_D, HIGH);
	digitalWrite(PIN_E, HIGH);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, LOW);
	digitalWrite(PIN_H, LOW);
}

void displayH()
{
	digitalWrite(PIN_A, LOW);
	digitalWrite(PIN_B, HIGH);
	digitalWrite(PIN_C, HIGH);
	digitalWrite(PIN_D, LOW);
	digitalWrite(PIN_E, HIGH);
	digitalWrite(PIN_F, HIGH);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void displayDash()
{
	digitalWrite(PIN_A, LOW);
	digitalWrite(PIN_B, LOW);
	digitalWrite(PIN_C, LOW);
	digitalWrite(PIN_D, LOW);
	digitalWrite(PIN_E, LOW);
	digitalWrite(PIN_F, LOW);
	digitalWrite(PIN_G, HIGH);
	digitalWrite(PIN_H, LOW);
}

void displayNumber(int number)
{
	if(number < 0 || number > 9) return;

	switch (number)
	{
	case 1:
		display1();
		break;
	case 2:
		display2();
		break;
	case 3:
		display3();
		break;
	case 4:
		display4();
		break;
	case 5:
		display5();
		break;
	case 6:
		display6();
		break;
	case 7:
		display7();
		break;
	case 8:
		display8();
		break;
	case 9:
		display9();
		break;
	case 0:
		display0();
		break;
	}
}

int getDigit(float* value)
{
	int result = 0;
	if (*value > 1000)
	{
		result = (int)*value / 1000;
		*value -= result * 1000;
	}else if (*value > 100)
	{
		result = (int)*value / 100;
		*value -= result * 100;
	}else if (*value > 10)
	{
		result = (int)*value / 10;
		*value -= result * 10;
	}else if (*value > 1)
	{
		result = (int)*value / 1;
		*value -= result;
	}else
	{
		result = ((int)*value * 10) / 1;
		*value -= result * 0.1;
	}

	return result;
}

void displayValueTemperature(float value){
	int i;
	boolean dotted = false;

	if (value >= 100 || value < -100)
	{
		for(i = 1; i <= 4; i++)
		{
			clearLED();
			pickDigit(i);
			displayDash();
			delayMicroseconds(DELAY_VALUE);
		}
	}else
	{
		int indexForDigit = 0;
		int shiftedValue = (int)(value * 10);
		int splitedValue[3] = {};
		
		splitedValue[0] = ((shiftedValue/100)%10);
		splitedValue[1] = ((shiftedValue/10)%10);
		splitedValue[2] = (shiftedValue%10);
		
		/*
		>=10
		xx.xc
			
		> 0
		_x.xc
		
		< 0 > -9.9
		-x.xc
		
		<-9.9
		-xx.x
		*/

		if(value > 0)
		{
			if(value >= 10)
			{
				clearLED();
				pickDigit(1);
				displayNumber(splitedValue[0]);
				delayMicroseconds(DELAY_VALUE);
			}

			clearLED();
			pickDigit(2);
			displayNumber(splitedValue[1]);
			displayDot();
			delayMicroseconds(DELAY_VALUE);

			clearLED();
			pickDigit(3);
			displayNumber(splitedValue[2]);
			delayMicroseconds(DELAY_VALUE);

			clearLED();
			pickDigit(4);
			displayC();
			delayMicroseconds(DELAY_VALUE);
		}else
		{
			clearLED();
			pickDigit(1);
			displayDash();
			delayMicroseconds(DELAY_VALUE);

			if(value > -10)
			{
				clearLED();
				pickDigit(2);
				displayNumber(splitedValue[1]);
				displayDot();
				delayMicroseconds(DELAY_VALUE);

				clearLED();
				pickDigit(3);
				displayNumber(splitedValue[2]);
				delayMicroseconds(DELAY_VALUE);

				clearLED();
				pickDigit(4);
				displayC();
				delayMicroseconds(DELAY_VALUE);
			}else
			{
				clearLED();
				pickDigit(2);
				displayNumber(splitedValue[0]);
				delayMicroseconds(DELAY_VALUE);

				clearLED();
				pickDigit(3);
				displayNumber(splitedValue[1]);
				displayDot();
				delayMicroseconds(DELAY_VALUE);

				clearLED();
				pickDigit(4);
				displayNumber(splitedValue[2]);
				delayMicroseconds(DELAY_VALUE);
			}
		}
		
		/*i = 1;
		if(splitedValue[0] == 0)
		{
			i = 2;
			indexForDigit++;
		}
		for(; i <= 4; i++)
		{
			clearLED();
			pickDigit(i);
			
			displayNumber(splitedValue[indexForDigit++]);
			delayMicroseconds(DELAY_VALUE);

			if(value < 1 && !dotted)
			{
				dotted = true;
				displayDot();
			}
		}*/
	}
}

void displayValueHumidity(float value){
	int i;
	boolean dotted = false;

	if (value >= 100 || value < 0)
	{
		for(i = 1; i <= 4; i++)
		{
			clearLED();
			pickDigit(i);
			displayDash();
			delayMicroseconds(DELAY_VALUE);
		}
	}else
	{
		int indexForDigit = 0;
		int shiftedValue = (int)(value * 10);
		int splitedValue[3] = {};
		
		splitedValue[0] = ((shiftedValue/100)%10);
		splitedValue[1] = ((shiftedValue/10)%10);
		splitedValue[2] = (shiftedValue%10);
		
		/*
		>=10
		xx.xc
			
		> 0
		_x.xc
		
		< 0 > -9.9
		-x.xc
		
		<-9.9
		-xx.x
		*/

		clearLED();
		pickDigit(1);
		displayH();
		delayMicroseconds(DELAY_VALUE);

		if(value >= 10)
		{
			clearLED();
			pickDigit(2);
			displayNumber(splitedValue[0]);
			delayMicroseconds(DELAY_VALUE);
		}

		clearLED();
		pickDigit(3);
		displayNumber(splitedValue[1]);
		displayDot();
		delayMicroseconds(DELAY_VALUE);

		clearLED();
		pickDigit(4);
		displayNumber(splitedValue[2]);
		delayMicroseconds(DELAY_VALUE);
		
		/*i = 1;
		if(splitedValue[0] == 0)
		{
			i = 2;
			indexForDigit++;
		}
		for(; i <= 4; i++)
		{
			clearLED();
			pickDigit(i);
			
			displayNumber(splitedValue[indexForDigit++]);
			delayMicroseconds(DELAY_VALUE);

			if(value < 1 && !dotted)
			{
				dotted = true;
				displayDot();
			}
		}*/
	}
}

void controlRelay()
{
	if (dhtTemperature < relayTiggerOn)
	{
		digitalWrite(RELAY_PIN, RELAY_ON);
	}else if (dhtTemperature > relayTiggerOff)
	{
		digitalWrite(RELAY_PIN, RELAY_OFF);
	}
}

void getData()
{
	lastGetData = millis();

	humidity = dht.getHumidity();
	dhtTemperature = dht.getTemperature();
	bmpTemperature = bmp.readTemperature();
	pressure = bmp.readPressure();

	controlRelay();

	showTemperature = !showTemperature;

	Serial.print("DHT Temperature: ");
	Serial.print(dhtTemperature);
	Serial.print(", humidity: ");
	Serial.print(humidity);
	Serial.print(", bmp_temperature: ");
	Serial.print(bmpTemperature);
	Serial.print(", pressure: ");
	Serial.println(pressure);

	Serial.print("Show temerature value: ");
	Serial.println(showTemperature);
}


void sendResult()
{
	lastSendData = millis();

	mySerial.print("{\"dht_temperature\": ");
	mySerial.print(dhtTemperature);

	mySerial.print(", \"humidity\": ");
	mySerial.print(humidity);

	mySerial.print(", \"bmp_temperature\": ");
	mySerial.print(bmpTemperature);

	mySerial.print(", \"pressure\": ");
	mySerial.print(pressure);

	mySerial.print("}");
	mySerial.println("");
	//mySerial.flush();
}

void processJsonData(char *jsonString)
{
	aJsonObject* jsonRoot = aJson.parse(jsonString);

	// return if can't parse data.
	if(jsonRoot == NULL)
	{
		Serial.println("Parse JSON error.");
		return;
	}

	aJsonObject* jsonSerial = aJson.getObjectItem(jsonRoot, "serial");
	aJsonObject* jsonLow = aJson.getObjectItem(jsonRoot, "low");
	aJsonObject* jsonHigh = aJson.getObjectItem(jsonRoot, "high");

	if(jsonSerial->valueint > serialNumber)
	{
		if(jsonHigh->valuefloat > jsonLow->valuefloat && (jsonHigh->valuefloat - jsonLow->valuefloat) > RELAY_CONTROL_TEMPERATURE_DIFFERENT)
		{
			relayTiggerOn = jsonLow->valuefloat;
			relayTiggerOff = jsonHigh->valuefloat;
		}
	}

	aJson.deleteItem(jsonRoot);
}

void readConfig()
{
	if(mySerial.available() > 0)
	{
		i = 0;
		while (mySerial.available() > 0)
		{
			temp = mySerial.read();
			if(temp == '\n')
			{
				readBuffer[i++] = '\0';

				// when reach newline, means no needed data, so clear buffer.
				//while (mySerial.available() > 0) mySerial.read();
				mySerial.flush();
			}else
			{
				readBuffer[i++] = temp;
			}
		}

		Serial.print("Read this from server: ");
		Serial.println(readBuffer);

		processJsonData(readBuffer);

		readBuffer[0] = '\0';
	}else
	{
		Serial.println("Nothing from server.");
	}
}

void setLedOn()
{
	int index;
	for(index=PIN_A; index<=PIN_H;index++)
	{
		pinMode(index, OUTPUT);
	}

	for(index=PIN_DIGI1; index<=PIN_DIGI4;index++)
	{
		pinMode(index, OUTPUT);
	}
}

void setLedOff()
{
	int index;
	for(index=PIN_A; index<=PIN_H;index++)
	{
		pinMode(index, INPUT);
	}

	for(index=PIN_DIGI1; index<=PIN_DIGI4;index++)
	{
		pinMode(index, INPUT);
	}

	clearLED();
}

void setup()
{
	Serial.begin(9600);
	mySerial.begin(9600);

	dht.setup(DHT22_PIN);

	pinMode(RELAY_PIN, OUTPUT);
	digitalWrite(RELAY_PIN, RELAY_OFF);

	setLedOn();

	bmp.begin();

	showTemperature = false;

	relayTiggerOn = RELAY_TRIGGER_ON;
	relayTiggerOff = RELAY_TRIGGER_OFF;

	serialNumber = -1;

	getData();
	
	sendResult();
}

void loop()
{
	currentTime = millis();

	if((currentTime - lastGetData) >= GET_DATA_INTERVAL)
	{
		getData();
	}else if (currentTime < lastGetData)
	{
		lastGetData = currentTime;
	}

	if((currentTime - lastSendData) >= SEND_DATA_INTERVAL)
	{
		sendResult();
		readConfig();
	}else if (currentTime < lastSendData)
	{
		// when timer overflow, set lastSendData to current. 
		lastSendData = currentTime;
	}
	

	//sendResult(dht_temperature, humidity, bmp_temperature, pressure);
	
	/*if (millis() < lastGetData)
	{
		toDelay = INTERVAL - ((UNSIGNED_LONG_MAX - lastGetData) + millis());
	}else
	{
		toDelay = INTERVAL - (millis() - lastGetData);
	}
	
	if(toDelay > INTERVAL) toDelay = INTERVAL;
	
	delay(toDelay);*/

	if(showTemperature)
	{
		displayValueTemperature(dhtTemperature);
	}else
	{
		displayValueHumidity(humidity);
	}

	/*while(mySerial.available())
	{
		Serial.print(mySerial.read());
	}

	while(Serial.available())
	{
		mySerial.print(Serial.read());
	}*/
}