async function uploadFile(){

let fileInput=document.getElementById("fileInput")

let formData=new FormData()

formData.append("file",fileInput.files[0])

let response=await fetch("/upload",{

method:"POST",

body:formData

})

let data=await response.json()

alert(data.message)

}



async function sendMessage(){

let message=document.getElementById("message").value

let chatbox=document.getElementById("chatbox")

chatbox.innerHTML+=`<div class="user">${message}</div>`

let response=await fetch("/chat",{

method:"POST",

headers:{

"Content-Type":"application/json"

},

body:JSON.stringify({

message:message

})

})

let data=await response.json()

chatbox.innerHTML+=`<div class="bot">${data.reply}</div>`

document.getElementById("message").value=""

chatbox.scrollTop=chatbox.scrollHeight

}