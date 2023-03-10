const BASE_PATH = ''

window.onload = function () {
	// check if already logged in
	if(localStorage.getItem('loggedIn'))
	{
		showHomePage();
	}
	else
	{
		showLoginPage();
	}
}

function login()
{
	function loadedEventCallback()
	{
		console.log('status =' +xhr.status)

		if(xhr.status == 200)
		{
			localStorage.setItem('loggedIn', document.getElementById('username').value);
			showHomePage();
		}
	}
	
	var xhr = new XMLHttpRequest();
	xhr.addEventListener("load", loadedEventCallback);
	path = '/api/login'
	xhr.open("POST", path, true);
	xhr.setRequestHeader('Content-Type', 'text/html');
	xhr.send(JSON.stringify({
		username: document.getElementById('username').value ,
		password: document.getElementById('password').value
	}));
	
}

function logout()
{
	function loadedEventCallback()
	{
		console.log('status =' +xhr.status)

		if(xhr.status == 200)
		{
			localStorage.removeItem('loggedIn');
			showLoginPage();
			table = document.getElementById('tweetTable');
			table.innerHTML="";
		}
	}
	

	var xhr = new XMLHttpRequest();
	xhr.addEventListener("load", loadedEventCallback);
	path = '/api/logout'
	xhr.open("DELETE", path, true);
	xhr.send()
}

function getTweets()
{

	function loadedEventCallback()
	{
		console.log('status =' +xhr.status)

		if(xhr.status == 200)
		{
			var tweets = JSON.parse(xhr.responseText);
			console.log(tweets)
			table = document.getElementById('tweetTable')
			table.innerHTML="";
			
			tweets.forEach(element => {
				console.log(element.id+': '+element.tweet+', '+element.byUser);
				tableEntry='<tr><td>'+element.byUser+'</td><td>'+element.tweet+'</td><td></td></tr>';
				var row = table.insertRow(0);

				// Insert new cells (<td> elements) at the 1st and 2nd position of the "new" <tr> element:
				var cell0 = row.insertCell(0);
				var cell1 = row.insertCell(1);
				var cell2 = row.insertCell(2);

				// Add some text to the new cells:
				if(localStorage.getItem('loggedIn') == element.byUser)
				{
					cell0.innerHTML = "<button type='button' class='deleteTweet' id='"+element.id+"' onclick='deleteTweet(this.id)'>DELETE</button>";
				}
				else
				{
					cell0.innerHTML = '';
				}
				cell1.innerHTML = element.byUser+': ';
				cell2.innerHTML = element.tweet;
			});
			
		}
	}
	

	var xhr = new XMLHttpRequest();
	xhr.addEventListener("load", loadedEventCallback);
	path = '/api/tweet'
	xhr.open("GET", path, true);
	xhr.send();
}

function postTweet()
{
	theTweet = (document.getElementById('newTweet').value).trim();
	document.getElementById('newTweet').value = ''
	if(theTweet.length > 0)
	{
		function loadedEventCallback()
		{
			console.log('status =' +xhr.status)

			if(xhr.status == 200)
			{
				getTweets();
			}
		}
	
	
		var xhr = new XMLHttpRequest();
		xhr.addEventListener("load", loadedEventCallback);
		path = '/api/tweet'
		xhr.open("POST", path, true);
		xhr.setRequestHeader('Content-Type', 'text/html');
		xhr.send(JSON.stringify({
			tweet: theTweet
		}));
	}
}

function deleteTweet(tweetID)
{
	console.log(tweetID);
	function loadedEventCallback()
	{
		console.log('status =' +xhr.status)

		if(xhr.status == 200)
		{
			getTweets();
		}
	}
	

	var xhr = new XMLHttpRequest();
	xhr.addEventListener("load", loadedEventCallback);
	path = '/api/tweet/'+tweetID
	xhr.open("DELETE", path, true);
	xhr.send();
}

function showLoginPage()
{
	document.body.style.background = "Snow";
	visibility(0, 'homepage');
	visibility(1, 'loginContainer'); // show login fields
}

function showHomePage()
{
	console.log(localStorage.getItem('loggedIn'));	

	document.body.style.background = "PapayaWhip";
	document.getElementById('theTitle').innerHTML = ('Welcome back '+localStorage.getItem('loggedIn')+'!')
	visibility(0, 'loginContainer');
	visibility(1, 'homepage'); // show homepage
	
	getTweets()
}

function visibility(toShow, id){
	var theElement = document.getElementById(id)
	
	if(theElement)
	{	
		if(toShow == 0)
		{
			theElement.style.display = 'none';
		}
		else if(toShow == 1)
		{
			theElement.style.display = 'block';
		}
	}
}
