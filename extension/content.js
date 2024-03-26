(async () => {
    chrome.runtime.onMessage.addListener((request, sender, response) => {
        if (request.message === "GetContent") {
            var documentClone = document.cloneNode(true);
            var article = new Readability(documentClone).parse();
            var content = article.textContent;
            content = content.replace(/(\r\n|\n|\r)/gm, " ");
            
            response({contentRetrieved: content});
        }
    })
})();

