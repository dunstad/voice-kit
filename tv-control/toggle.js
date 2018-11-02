var PanasonicViera = require('panasonic-viera-control/panasonicviera');
var tv = new PanasonicViera('192.168.0.122');
tv.send(PanasonicViera.POWER_TOGGLE);

