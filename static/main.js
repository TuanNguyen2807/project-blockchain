(async function() {
    const mine = document.getElementById("mine");
    const chain = document.getElementById("chain");
    const transparent = document.getElementById("transparent");

    const add = document.getElementById("add");
  
    const sender = document.getElementById("usr").innerText;
    const recipient = document.getElementById("recipient");
    const amount = document.getElementById("amount");
    const content = document.getElementById("content");
  
    mine.addEventListener("click", async () => {
        var xhttp = new XMLHttpRequest();
        xhttp.open("get", "http://127.0.0.1:5000/mine", true);
        xhttp.send("mine");

        xhttp.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
              recvData = JSON.parse(this.responseText);
              if(recvData) {
                console.log(recvData);
              }
            } else {
              console.log("error while receiving data");
            }
        }
    });
  
    chain.addEventListener("click", async () => {
      var xhttp = new XMLHttpRequest();
        xhttp.open("get", "http://127.0.0.1:5000/chain", true);
        xhttp.send("chain");

        xhttp.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
              recvData = JSON.parse(this.responseText);
              if(recvData) {
                console.dir(recvData);
              }
            } else {
              console.log("error while receiving data");
            }
        }
    });
  
    // transparent.addEventListener("click", async () => {
      
    // });
  
    // library2.addEventListener("click", async () => {
    //   var xhttp = new XMLHttpRequest();
    //   xhttp.open("post", "http://127.0.0.1:5000/mine", true);
    //   xhttp.send("mine");
    
    //   var result = document.getElementById('result');
  
    //   while (result.firstChild) {
    //     result.removeChild(result.lastChild);
    //   }
  
    //   xhttp.onreadystatechange = function() {
    //     if(this.readyState == 4 && this.status == 200) {
    //       recvData = this.responseText;
    //       const recvArr = recvData.split(",");
    //       for (const element of recvArr) {
    //         // var node = document.createElement("LI");
    //         // var textnode = document.createTextNode(element);
    //         // node.appendChild(textnode);
    //         // document.getElementById("result").appendChild(node);
    //         var newDiv = document.createElement("div");
    //         var newline = document.createElement('br');
    //         var newlabel = document.createElement('label');
    //         newlabel.innerHTML = element;
    //         var newinput = document.createElement('input');
    //         newinput.className = "abcdef";
    //         newinput.type = "radio";
    //         newinput.name = "lib";
    //         newinput.id = element;
    //         newinput.value = element;
    //         newDiv.appendChild(newinput);
    //         newDiv.appendChild(newlabel);
    //         newDiv.appendChild(newline);
    //         document.getElementById("result").appendChild(newDiv);
    //       }
    //     } else {
    //       console.log("error while receiving data");
    //     }
    //   }
    // });
    
    add.addEventListener("click", function (e) {
      
      var obj = {
        sender: `${sender}`, 
        recipient: `${recipient.value.toString()}`, 
        amount: `${amount.value.toString()}`, 
        content: `${content.value.toString()}` 
      };
      var strObj = JSON.stringify(obj);
      console.log(strObj);
      var jsonObj = JSON.parse(strObj);
      console.log(jsonObj);

      var xhttp = new XMLHttpRequest();
      xhttp.open("post", "http://127.0.0.1:5000/transactions", true);
      xhttp.send(strObj);

      xhttp.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
          recvData = JSON.parse(this.response);
          console.log(recvData.message);
        } else {
          console.log("error while receiving data");
        }
    }
    });
  
  })();
  
 
  