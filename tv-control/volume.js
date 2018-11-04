var PanasonicViera = require('panasonic-viera-control/panasonicviera');
var tv = new PanasonicViera('192.168.0.22');
tv.setVolume(process.argv[2]);

