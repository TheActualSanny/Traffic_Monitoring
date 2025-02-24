function insertLookup(lookup) {
    lookupsDiv = document.getElementById('accounts');
    content = document.createElement('p');
    profileLink = document.createElement('a');
    lookupInstance = document.createElement('div');
    lookupInstance.setAttribute('id', 'lookup-instance');
    url = Object.keys(lookup)[0];
    content.textContent = `${lookup[url]}`;
    profileLink.href = `https://${url}`;
    profileLink.textContent = url;
    lookupInstance.appendChild(profileLink);
    lookupInstance.appendChild(content);
    lookupsDiv.appendChild(lookupInstance);
}


let url = `ws://${window.location.host}/ws/lookup-server/`;
const socket = new WebSocket(url);

socket.onmessage = function(e) {
    data = JSON.parse(e.data);  
    if (data.lookup_data){
        var lookups = data.lookup_data;
        insertLookup(lookups);
        
    }    
}
