function GetContent(activeTab) {
    chrome.tabs.sendMessage(activeTab.id, {message: "GetContent"}, (response) => {
        if (response) {
            document.getElementById("content").value = response.contentRetrieved;
        }
    });
}

chrome.runtime.onMessage.addListener((request, sender, response) => {
    document.getElementById("content").value = response.contentRetrieved;
});

(async () => {
    chrome.tabs.onActivated.addListener(async (activeInfo) => {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        if (tab.active) {   
            document.getElementById("lastaction").innerText = "tab activated";
            GetContent(tab);
        }
    });

    chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
        document.getElementById("lastaction").innerText = "tab updated";
        GetContent(tab);
    });
})();

window.onload=function() {
    document.getElementById("RetrieveAudio").addEventListener("click", function() { 
        document.getElementById("loader").style.visibility = "visible";
        document.getElementById("audio").style.visibility = "hidden";
        document.getElementById("lastaction").innerText = "Retrieving audio";

        fetch("https://talktomefunction.azurewebsites.net/api/GenerateConversation?code=<<replace with your function key>>", 
            { 
                method: "POST", 
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg"
                },
                body: JSON.stringify({ "content": document.getElementById("content").value })
            })
          .then(response => response.blob())
          .then(blob => {
            document.getElementById("audio").src = URL.createObjectURL(blob);

            document.getElementById("loader").style.visibility = "hidden";
            document.getElementById("audio").style.visibility = "visible";
          })
          .catch(err =>  {
            document.getElementById("lastaction").innerText = err;
            document.getElementById("loader").style.visibility = "hidden";
          });
    })
};
