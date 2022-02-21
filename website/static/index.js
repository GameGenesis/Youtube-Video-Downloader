function copyToClipboard(url) {
    navigator.clipboard.writeText(url);
}

function openInNewTab(url) {
    window.open(url, '_blank').focus();
}