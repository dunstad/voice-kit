// get tv power state first, only toggle if it's off
let PanasonicViera = require('panasonic-viera-control/panasonicviera');
let tv = new PanasonicViera('192.168.0.122');
tvIsOff = true;
tv.getMute((mute)=>{
  tvIsOff = false;
});

setTimeout(()=>{

  if (tvIsOff) {

    console.log('turning tv on')
    tv.send(PanasonicViera.POWER_TOGGLE);

  }

  startVideo();

}, 100);

function startVideo() {
  
  let words = process.argv.slice(2).join(' ');
  const YouTubeAPIKey = process.env.YOUTUBE;
  let search = require('youtube-search');
  
  let opts = {
    maxResults: 1,
    key: YouTubeAPIKey,
  };
  
  search(words, opts, (err, results)=>{
    if (err) {console.error(err);}
    else {
  
      let dial = require('peer-dial');
      let client = new dial.Client;
      client.getDialDevice('http://192.168.0.122:55000/nrc/ddd.xml', (device, err)=>{
        if (err) {
          console.error('error getting device');
          console.error(err);
        }
        else {
  
          device.stopApp("YouTube","run", (statusCode, err)=>{
            if (err) {
              console.error("Error on stop YouTube App:", err);
            }
            else {
              console.log("DIAL stop YouTube App status: ", statusCode);
            }
          });
  
          // setTimeout(()=>{
            device.launchApp("YouTube",`v=${results[0].id}`, "text/plain", function (launchRes, err) {
              if(typeof launchRes != "undefined"){
                console.log("YouTube Launched Successfully",launchRes);
              }
              else if(err){
                console.log("Error on Launch YouTube App",launchRes);
              }
            });
          // }, 100);
  
        }
      });
  
    }
  });

}


