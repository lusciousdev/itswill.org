const scriptData = document.currentScript.dataset;

const overallRecap = scriptData.overallrecap;
const recapApiURL = scriptData.getrecapdataurl;

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
  
  requestRecapData();
  setInterval(requestRecapData, 5000);
});
