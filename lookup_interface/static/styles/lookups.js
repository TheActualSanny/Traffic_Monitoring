function loadRecords() {
    fetch('/lookup_interface/lookup_records', {method : 'GET'})
    .then(res => {
        return res.json();
    })
    .then(finalized => {
        if (finalized.data){
            data = finalized.data;
            lookupsDiv = document.getElementById('accounts');

            for (let i = 0; i < data.length; i++){
                content = document.createElement('p');
                profileLink = document.createElement('a');
                lookupInstance = document.createElement('div');
                lookupInstance.setAttribute('id', 'lookup-instance');
                url = Object.keys(data[i])[0];
                content.textContent = `${data[i][url]}`;
                profileLink.href = `https://${url}`;
                profileLink.textContent = url;
                lookupInstance.appendChild(profileLink);
                lookupInstance.appendChild(content);
                lookupsDiv.appendChild(lookupInstance);
            }
        }
    })
    .catch(err => {
        clearInterval(loadLookups);
        console.log(err);
    })
}

const loadLookups = setInterval(loadRecords, 1000);