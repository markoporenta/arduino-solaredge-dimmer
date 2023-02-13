// Import required libraries
#include <ESP8266WiFi.h>
#include <ESPAsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <hw_timer.h>

// network credentials
const char* ssid = "imeSSID"; // ACCESS POINT
const char* password = "gesloSSID"; //ENTER PASSWORD IF DESIRED

// Set your Static IP address
IPAddress local_IP(192, 168, 58, 95);
// Set your Gateway IP address
IPAddress gateway(192, 168, 58, 1);

IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(192, 168, 58, 1);   //optional
IPAddress secondaryDNS(192, 168, 58, 1); //optional

// Pot. zc pins: D5, D6, D7
const byte zcPin = D5;
// Pot. PWM pins: D1, D2, D8
const byte pwmPin = D2;

const int ledpin = D4;

const double VCC = 3.3;             // NodeMCU on board 3.3v vcc
const double R2 = 10000;            // 10k ohm series resistor
const double adc_resolution = 1023; // 10-bit adc

const double A = 0.001129148;   // thermistor equation parameters
const double B = 0.000234125;
const double C = 0.0000000876741; 

byte tarBrightness = 255;
byte zcPending = 0; // 0 = ready; 1 = processing;
void ICACHE_RAM_ATTR zcDetectISR ();
void ICACHE_RAM_ATTR dimTimerISR ();

String sliderValue = "0";
double temperature = 0;

const char* PARAM_INPUT = "value";

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Power controller</title>
  <style>
    html {font-family: Arial; display: inline-block; text-align: center;}
    h2 {font-size: 2.3rem;}
    p {font-size: 1.9rem;}
    body {max-width: 400px; margin:0px auto; padding-bottom: 25px;}
    .slider { -webkit-appearance: none; margin: 14px; width: 360px; height: 25px; background: #FFD65C;
      outline: none; -webkit-transition: .2s; transition: opacity .2s;}
    .slider::-webkit-slider-thumb {-webkit-appearance: none; appearance: none; width: 35px; height: 35px; background: #003249; cursor: pointer;}
    .slider::-moz-range-thumb { width: 35px; height: 35px; background: #003249; cursor: pointer; } 
  </style>
</head>
<body>
  <h2>ESP Web Server</h2>
  <p><span id="textSliderValue">%SLIDERVALUE%</span></p>
  <p><input type="range" onchange="updateSliderPWM(this)" id="pwmSlider" min="0" max="255" value="%SLIDERVALUE%" step="1" class="slider"></p>
  <p>Temperature: %TEMP%</p>
<script>
function updateSliderPWM(element) {
  var sliderValue = document.getElementById("pwmSlider").value;
  document.getElementById("textSliderValue").innerHTML = sliderValue;
  console.log(sliderValue);
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/slider?value="+sliderValue, true);
  xhr.send();
}
</script>
</body>
</html>
)rawliteral";

// Replaces placeholder with button section in your web page
String processor(const String& var){
  //Serial.println(var);
  if (var == "SLIDERVALUE"){
    return sliderValue;
  }
  if (var == "TEMP"){
    return String(temperature,2);
  }
  return String();
}

const double lindelay[256] = {
1.000000,0.960185,0.943657,0.930949,0.920214,0.910737,0.902153,0.894243,0.886866,0.879923,0.873343,0.867072,0.861068,0.855297,0.849733,0.844353, // 0 - 15
0.839139,0.834075,0.829147,0.824345,0.819657,0.815075,0.810592,0.806200,0.801894,0.797667,0.793515,0.789433,0.785418,0.781464,0.777570,0.773732, // 16 - 31
0.769947,0.766212,0.762525,0.758883,0.755285,0.751729,0.748213,0.744734,0.741292,0.737885,0.734511,0.731169,0.727858,0.724577,0.721325,0.718100, // 32 - 47
0.714901,0.711728,0.708580,0.705455,0.702353,0.699274,0.696215,0.693178,0.690160,0.687162,0.684183,0.681221,0.678278,0.675351,0.672440,0.669546, // 48 - 63
0.666667,0.663803,0.660953,0.658117,0.655295,0.652487,0.649691,0.646907,0.644136,0.641376,0.638628,0.635891,0.633164,0.630447,0.627741,0.625044, // 64 - 79
0.622357,0.619679,0.617010,0.614350,0.611697,0.609053,0.606417,0.603788,0.601166,0.598552,0.595944,0.593344,0.590749,0.588161,0.585578,0.583002, // 80 - 95
0.580431,0.577865,0.575304,0.572749,0.570198,0.567652,0.565110,0.562572,0.560038,0.557509,0.554983,0.552460,0.549941,0.547424,0.544911,0.542401, // 96 - 111
0.539893,0.537388,0.534885,0.532384,0.529885,0.527389,0.524893,0.522400,0.519907,0.517416,0.514926,0.512437,0.509949,0.507461,0.504974,0.502487, // 112 - 127
0.500000,0.497513,0.495026,0.492539,0.490051,0.487563,0.485074,0.482584,0.480093,0.477600,0.475107,0.472611,0.470115,0.467616,0.465115,0.462612, // 128 - 143
0.460107,0.457599,0.455089,0.452576,0.450059,0.447540,0.445017,0.442491,0.439962,0.437428,0.434890,0.432348,0.429802,0.427251,0.424696,0.422135, // 144 - 159
0.419569,0.416998,0.414422,0.411839,0.409251,0.406656,0.404056,0.401448,0.398834,0.396212,0.393583,0.390947,0.388303,0.385650,0.382990,0.380321, // 160 - 175
0.377643,0.374956,0.372259,0.369553,0.366836,0.364109,0.361372,0.358624,0.355864,0.353093,0.350309,0.347513,0.344705,0.341883,0.339047,0.336197, // 176 - 191
0.333333,0.330454,0.327560,0.324649,0.321722,0.318779,0.315817,0.312838,0.309840,0.306822,0.303785,0.300726,0.297647,0.294545,0.291420,0.288272, // 192 - 207
0.285099,0.281900,0.278675,0.275423,0.272142,0.268831,0.265489,0.262115,0.258708,0.255266,0.251787,0.248271,0.244715,0.241117,0.237475,0.233788, // 208 - 223
0.230053,0.226268,0.222430,0.218536,0.214582,0.210567,0.206485,0.202333,0.198106,0.193800,0.189408,0.184925,0.180343,0.175655,0.170853,0.165925, // 224 - 239
0.160861,0.155647,0.150267,0.144703,0.138932,0.132928,0.126657,0.120077,0.113134,0.105757,0.097847,0.089263,0.079786,0.069051,0.056343,0.039815 // 240 - 255
};

void setup(){
// Serial port for debugging purposes
Serial.begin(115200);

//WiFi.softAP(ssid, password);
//IPAddress IP = WiFi.softAPIP();
//Serial.println(IP);

// Configures static IP address
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("STA Failed to configure");
  }

  // Connect to Wi-Fi network with SSID and password
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  //server.begin();

pinMode(zcPin, INPUT);
pinMode(pwmPin, OUTPUT);
pinMode(ledpin, OUTPUT);
attachInterrupt(zcPin, zcDetectISR, RISING); // Attach an Interupt to Pin (interupt 0) for Zero Cross Detection
hw_timer_init(NMI_SOURCE, 0);
hw_timer_set_func(dimTimerISR);
  
// Route for root / web page
server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    readThermistor();
    request->send_P(200, "text/html", index_html, processor);
});

// Send a GET request to <ESP_IP>/slider?value=
server.on("/slider", HTTP_GET, [] (AsyncWebServerRequest *request) {
  String inputMessage;

  readThermistor();
  
  // GET input1 value on <ESP_IP>/slider?value=
  if (request->hasParam(PARAM_INPUT)) {
    inputMessage = request->getParam(PARAM_INPUT)->value();
    sliderValue = inputMessage;
  } else {
    inputMessage = "No message sent";
  }

  Serial.print("Slider: "); Serial.println(inputMessage);
  request->send(200, "text/plain", "OK");
            
  Serial.print("Temperature:"); Serial.println(temperature);     
});

// Start server
server.begin();

}

void loop() {
  int val;
 
  val = sliderValue.toInt();
  if (val >= 0){
    tarBrightness = val;
  }  

}

void dimTimerISR() {

  if (tarBrightness > 0) {
    digitalWrite(pwmPin, 1);digitalWrite(ledpin, 1);  
  }
  delayMicroseconds(100);
  digitalWrite(pwmPin, 0);digitalWrite(ledpin, 0);  
    
  zcPending = 0;
 
}

void zcDetectISR() {

  if (zcPending == 0) {
      
    if (tarBrightness < 256 && tarBrightness > 0) {
      // Linear delay
      //int dimDelay = 30 * (256 - tarBrightness) + 400;//400
      // Linear power using acos, too much delay ?
      //int dimDelay = 30 * (acos((double)(((double)tarBrightness-128)/256)) * 256 /3.14) + 400;
      // Linear power using acos table, seems acos too slow
      //int dimDelay = 30 * (256 - tarBrightness) + 400;//400
      zcPending = 1;
      int dimDelay = 10000 * lindelay[tarBrightness];
      hw_timer_arm(dimDelay);
    } 

  }
}

void readThermistor()
{
  //Thermistor readings
  double Vout, Rth, adc_value; 
  adc_value = analogRead(A0);
  Vout = (adc_value * VCC) / adc_resolution;
  Rth = (VCC * R2 / Vout) - R2;

/*  Steinhart-Hart Thermistor Equation:
 *  Temperature in Kelvin = 1 / (A + B[ln(R)] + C[ln(R)]^3)
 *  where A = 0.001129148, B = 0.000234125 and C = 8.76741*10^-8  */
  temperature = (1 / (A + (B * log(Rth)) + (C * pow((log(Rth)),3))));   // Temperature in kelvin
  temperature = temperature - 273.15;  // Temperature in degrees celsius
  Serial.print("Temperature calc:"); Serial.println(temperature);     
  
}
