# Steam Inventory Liquidator

A script to sell everything in your Steam inventory. Or at least, it sells everything in mine, YMMV.

## Usage

1. Install [Pipenv](https://docs.pipenv.org/) (`pip install pipenv`)
2. Clone this repo (and cd into the directory)
3. Run `pipenv install` to install the project dependencies
4. Run the script with `pipenv run python main.py`
5. Enter your username, password, and the authentication code from your email/authenticator app as prompted

## Warning

Although this script is pretty safe, and won't do anything other than send sell requests for your
items, you can get temporary locked out of steam if you fail to log in too many times in a row, as I
learned developing the login parts. However, if you avoid that issue, there's no problem running the script
as many times as you like; after all, you can only sell things once!

## Feature Requessts

I will not be doing any more work on this for a while, having successfully cleaned out all my stuff. However,
you're welcome to fork it, and I invite you to send a PR over so others can benefit.

## Contributions

* Thanks to @bbbates for adding Steam Authenticator support

## License

This software is released under the DWTFYWT Public License v2:

```
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                   Version 2, December 2004
 
Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

Everyone is permitted to copy and distribute verbatim or modified
copies of this license document, and changing it is allowed as long
as the name is changed.
 
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
  TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

 0. You just DO WHAT THE FUCK YOU WANT TO.
 ```
