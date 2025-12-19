const scriptData = document.currentScript.dataset;

const overallRecap = scriptData.overallrecap;
const recapApiURL = scriptData.getrecapdataurl;
const fiveRecordURL = scriptData.fiverecordurl;

var g_Websocket;
var g_ReconnectInterval = undefined;

function timeToPrettyString(timeInt, abbreviate = false)
{
  var days = Math.floor(timeInt / (3600 * 24));
  var rem = timeInt % (3600 * 24);

  var hours = Math.floor(rem / 3600);
  var rem = rem % 3600;

  var minutes = Math.floor(rem / 60);
  var rem = rem % 60;

  var seconds = rem;

  var output = "";

  var msd_hit = false;
  if (days > 0)
  {
    if (abbreviate)
      output += days.toLocaleString() + "d ";
    else
      output += days.toLocaleString() + " days, ";

    msd_hit = true;
  }

  if (msd_hit || hours > 0)
  {
    if (abbreviate)
      output += hours.toLocaleString() + "h ";
    else
      output += hours.toLocaleString() + " hours, ";

    msd_hit = true;
  }

  if (msd_hit || minutes > 0)
  {
    if (abbreviate)
      output += minutes.toLocaleString() + "m " + seconds.toLocaleString() + "s";
    else
      output += minutes.toLocaleString() + " minutes and " + seconds.toLocaleString() + " seconds";

    msd_hit = true;
  }

  if (!msd_hit)
  {
    if (abbreviate)
      output += seconds.toLocaleString() + "s"
    else
      output += seconds.toLocaleString() + " seconds"
  }

  return output
}

function handleWebsocketMessage(e)
{
  var eventData = JSON.parse(e.data);
  
  $(".messages").html(eventData["count_messages"].toLocaleString());
  $(".characters").html(eventData["count_characters"].toLocaleString());
  $(".chatters").html(eventData["count_chatters"].toLocaleString());
  $(".typing-time").html(timeToPrettyString(Math.floor(eventData["count_characters"] / 5), false));
  
  if (eventData["last_message"] !== null)
  {
    $(".last_message").html(eventData["last_message"]["message"]);
    $(".last_chatter").html(eventData["last_message"]["commenter"]["display_name"]);
  }
  else
  {
    $(".last_message").html("NO LAST MESSAGE");
    $(".last_chatter").html("NO ONE");
  }

  for (const [key, val] of Object.entries(eventData["counters"]))
  {
    $("." + key).html(val["total"].toLocaleString());

    for (const [fragKey, fragVal] of Object.entries(val["members"]))
    {
      cleanKey = fragKey.replace("+", "\\+");
      $("." + cleanKey).html(fragVal.toLocaleString());
    }
  }
}

function attemptWebsocketReconnect(e)
{
  if (g_ReconnectInterval == undefined)
  {
    g_ReconnectInterval = setInterval(() => { 
      if (g_Websocket.readyState == WebSocket.OPEN)
      {
        console.log("Reconnected websocket.");
        clearInterval(g_ReconnectInterval);
        g_ReconnectInterval = undefined;
        return;
      }
  
      console.log("Attempting to reconnect websocket.");
      connectWebsocket();
    }, 5000);
  }
}

function connectWebsocket()
{
  var protocol = "ws:"
  if (window.location.protocol == "https:")
    protocol = "wss:"
  g_Websocket = new WebSocket("{0}//{1}/ws/recap/{2}/".format(protocol, window.location.host, 2025));

  g_Websocket.onopen = (e) => {};
  g_Websocket.onmessage = (e) => { handleWebsocketMessage(e); };
  g_Websocket.onclose = (e) => { attemptWebsocketReconnect(e); };
}


function handleRecapData(respData)
{
  $(".messages").html(respData["count_messages"].toLocaleString());
  $(".characters").html(respData["count_characters"].toLocaleString());
  $(".typing-time").html(timeToPrettyString(Math.floor(respData["count_characters"] / 5), false));
  $("#clip-count-value").html(respData["count_clips"].toLocaleString());
  $("#clip-views-value").html(respData["count_clip_views"].toLocaleString());
  $("#clip-watch-value").html(timeToPrettyString(respData["count_clip_watch"], true));

  if (respData["first_message"] !== null)
  {
    $(".first_message").html(respData["first_message"]["message"]);
    $(".first_chatter").html(respData["first_message"]["commenter"]["display_name"]);
  }
  else
  {
    $(".first_message").html("NO LAST MESSAGE");
    $(".first_chatter").html("NO ONE");
  }

  if (respData["last_message"] !== null)
  {
    $(".last_message").html(respData["last_message"]["message"]);
    $(".last_chatter").html(respData["last_message"]["commenter"]["display_name"]);
  }
  else
  {
    $(".last_message").html("NO LAST MESSAGE");
    $(".last_chatter").html("NO ONE");
  }

  for (const [key, val] of Object.entries(respData["counters"]))
  {
    $("." + key).html(val["total"].toLocaleString());

    for (const [fragKey, fragVal] of Object.entries(val["members"]))
    {
      cleanKey = fragKey.replace("+", "\\+");
      $("." + cleanKey).html(fragVal.toLocaleString());
    }
  }
}

function handleFiveRecord(data)
{
  ontimePerc = data["on-time"] / data["total"];
  earlyPerc = data["early"] / data["total"];
  latePerc = 1 - ontimePerc - earlyPerc;

  if ($("#five-record").length != 0)
  {
    $("#early").html("Will went live early <b>{0}</b> times ({1} of streams)".format(data["early"], earlyPerc.toLocaleString(undefined, {style: "percent", maximumFractionDigits: 1})));
    $("#on-time").html("He went live on-time <b>{0}</b> times ({1} of streams)".format(data["on-time"], ontimePerc.toLocaleString(undefined, {style: "percent", maximumFractionDigits: 1})));
    $("#late").html("He was late for <b>{0}</b> streams ({1} of streams)".format(data["total"] - data["early"] - data["on-time"], latePerc.toLocaleString(undefined, {style: "percent", maximumFractionDigits: 1})));
    $("#total-streams").html("That puts us at <b>{0}</b> days streamed in 2025".format(data["total"]));
  }
}

function getFiveRecord()
{
  AjaxGet(fiveRecordURL, {}, handleFiveRecord, handleAjaxError);
}

function handleAjaxError(data)
{
  console.log("~~~~~~~~~~~ERROR~~~~~~~~~~~~~~~~~~~")
  console.log(data);
}

function requestRecapData()
{
  AjaxGet(recapApiURL, {}, handleRecapData, handleAjaxError);
}

$(window).on("load", function () {
  for (var key in extraData["chart_data"]) {
    var escapedKey = key.replace("+", "\\+");

    if ($("#{0}-chart".format(escapedKey)).length === 0)
      continue;

    const chartData = extraData["chart_data"][key];
    const chart = new Chart("{0}-chart".format(escapedKey), {
      type: "bar",
      data: {
        labels: chartData["labels"],
        datasets: chartData["datasets"],
      },
      options: {
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

  if (overallRecap == "1")
    connectWebsocket();

  requestRecapData();
  setInterval(requestRecapData, 10000);
  if ($("#five-record").length != 0)
  {
    getFiveRecord();
    var fiveRecordInterval = setInterval(getFiveRecord, 300000);
  }
});
