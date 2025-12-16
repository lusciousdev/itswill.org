const scriptData = document.currentScript.dataset;

const overallRecap = scriptData.overallrecap;
const recapApiURL = scriptData.getrecapdataurl;

var g_ExpandedStat = undefined;

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

function handleRecapData(respData)
{
  $("#msg-count-value").html(respData["count_messages"].toLocaleString());
  $("#char-count-value").html(respData["count_characters"].toLocaleString());
  $("#char-time-value").html(timeToPrettyString(Math.floor(respData["count_characters"] / 5), true));
  $("#clip-count-value").html(respData["count_clips"].toLocaleString());
  $("#clip-views-value").html(respData["count_clip_views"].toLocaleString());
  $("#clip-watch-value").html(timeToPrettyString(respData["count_clip_watch"], true));

  if (respData["first_message"] !== null)
  {
    var msg = "\"" + respData["first_message"]["message"] + "\"";
    if (overallRecap == "1")
    {
      msg += " - " + respData["first_message"]["commenter"]["display_name"]
    }
    $("#first-msg-value").html(msg);
  }
  else
  {
    $("#first-msg-value").html("<i>None</i>");
  }

  if (respData["last_message"] !== null)
  {
    var msg = "\"" + respData["last_message"]["message"] + "\"";
    if (overallRecap == "1")
    {
      msg += " - " + respData["last_message"]["commenter"]["display_name"]
    }
    $("#last-msg-value").html(msg);
  }
  else
  {
    $("#last-msg-value").html("<i>None</i>");
  }

  for (const [key, val] of Object.entries(respData["counters"]))
  {
    $("#" + key + "-value").html(val["total"].toLocaleString());

    for (const [fragKey, fragVal] of Object.entries(val["members"]))
    {
      cleanKey = fragKey.replace("+", "\\+");
      $("#" + cleanKey + "-value").html(fragVal.toLocaleString());
    }
  }
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

$(window).on('load', function() {
  $(".expand-stat").click(function (ev) {
    var targetId = $(ev.currentTarget).attr("group");

    $("#" + g_ExpandedStat + "-breakdown").css({ "max-height": "0px" });

    if (g_ExpandedStat != targetId)
    {
      var breakdownId = "#" + targetId + "-breakdown";
      var height = $(breakdownId).find(".stat-breakdown-table").height() + 18;
      $(breakdownId).css({ "max-height": String(height) + "px" });
      g_ExpandedStat = targetId;
    }
    else
    {
      g_ExpandedStat = undefined;
    }
  });

  requestRecapData();
  setInterval(requestRecapData, 5000);
});
