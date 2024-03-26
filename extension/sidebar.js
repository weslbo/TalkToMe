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
        document.getElementById("lastaction").innerText = "Retrieving audio";

        fetch("http://localhost:7071/api/retrieve_conversation?url=" + currentTab.url)
          .then(response => response.blob())
          .then(blob => {
            document.getElementById("audio").src = URL.createObjectURL(blob);
          })
          .catch(err =>  {
            document.getElementById("lastaction").innerText = err;
          });
    })
};
