function startLoading() {
    var loading = setInterval(loadMacs, 1000);
}

function removeDynamicMac(address) {

    fetch('/remove/', {method : 'POST', 
        headers : {
            'Content-Type' : 'application/json',
            'X-CSRFToken' : getToken('csrftoken')
        },
        body : JSON.stringify({address : address})
    })
    .then(res => res.json())
    .then(data => {
        if (data) {
            window.location.reload();
        }
    })
    .catch(err => {
        console.log(err);
    })
} 

function loadMacs() {
    fetch('/loadmacs', {method : 'GET'})
    .then(res => {
        return res.json();
    })
    .then(data => {
        if (data.entries) {
            all_entries = data.entries;
            main_div = document.getElementById('select-field');
            main_div.innerHTML = '';
            for (let i in all_entries){
                selectable = document.createElement('button');
                selectable.textContent = all_entries[i]['mac'];
                selectable.setAttribute('class', 'selectable-button');
                if (all_entries[i]['selected']){
                    selectable.setAttribute('id', 'mac-selected');
                }
                else {
                    selectable.setAttribute('id', 'mac-unselected');
                }
                macaddListener(selectable);
                main_div.appendChild(selectable);
            }
        }
    })
    .catch(err => {
        clearInterval(loadingMacs);
        console.log('Closed the server...');
    })
}



function interfaceField() {
    fetch("/update", {method : "GET"})
    .then(res => {
        return res.json();
    })
    .then(data => {
        console.log(data);
        interfaces = data.interfaces
        mainDiv = document.getElementById('interface-field');
        for (let i = 0; i < interfaces.length; i++){
            new_interface = document.createElement('button');
            new_interface.textContent = interfaces[i];
            new_interface.setAttribute('id', 'interface-instance');
            mainDiv.appendChild(new_interface);
            new_interface.addEventListener('click', function() {
                document.getElementById('id_network_interface').value = interfaces[i];
            });
        }
    })
    .catch(err => console.log(err))
}

function enable_storage() {
    if (document.getElementById('id_save_locally').checked){
        document.getElementById('id_traffic_directory').disabled = false;
    }
    else {
        document.getElementById('id_traffic_directory').disabled = true;
    }
}


function getToken(name) {
    var tokenValue = null;
    if (document.cookie && document.cookie !== ''){
        var cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            var currentCookie = cookies[i].trim();
            if (currentCookie.substring(0, name.length + 1) == (name + '=')){
                tokenValue = decodeURIComponent(currentCookie.substring(name.length + 1));
                break;
            }
        }
    }
    return tokenValue;
}
function macaddListener(button) {
            button.addEventListener('click', function() {
                var potential_mac = this.textContent;
                console.log(potential_mac);
                var selectedValue = this.getAttribute('id');
                if (selectedValue == 'mac-unselected'){
                    var postData = {
                        mac_address : potential_mac,
                        selected : true
                    }
                    button.style.backgroundColor = '#33CC78';
                } else {
                    var postData = {
                        mac_address : potential_mac,
                        selected : false
                    }
                    button.style.backgroundColor = '#D32C51';
                }

                fetch('/managemac/', {method : 'POST', 
                    headers : {
                        'Content-Type' : 'application/json',
                        'X-CSRFToken' : getToken('csrftoken')
                    },
                    body : JSON.stringify(postData)
                })
                .finally(() => {
                    if (selectedValue == 'mac-selected') {
                        removeDynamicMac(potential_mac);
                    }
                    else {
                        loadMacs();
                    }
                })
            });
    }

let url = `ws://${window.location.host}/ws/socket-server/`;
const chatSocket = new WebSocket(url);
chatSocket.onmessage = function(e) {
    let data = JSON.parse(e.data);
    if (data.packets) {
        arr = data.packets;
        console.log(arr);
        mainDiv = document.getElementById('packet-list');
        for(let i = 0; i < arr.length; i++){
                packetData = document.createElement('p');
                packetData.textContent = `Packet SRC IP: ${arr[i].src_ip}\n DST IP: ${arr[i].dst_ip}`;
                console.log(packetData.textContent);
                packetInstance = document.createElement('div');
                packetInstance.setAttribute('id', 'packet-instance');
                packetInstance.appendChild(packetData);
                mainDiv.appendChild(packetInstance);
        }
    }
    else {
        console.log(data);
    }
}

var addedButtons = [];  
var storeLocally = document.getElementById('id_save_locally');
var snifferButton = document.getElementById('begin'); 
var mac_invoker = document.getElementById('fetch-invoker');
mac_invoker.addEventListener('click', loadMacs);
storeLocally.addEventListener('change', enable_storage);
document.addEventListener('DOMContentLoaded', interfaceField);