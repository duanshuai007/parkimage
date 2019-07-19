#!/usr/bin/expect

set timeout 5

spawn ./addTask.sh
spawn service cron restart

expect "*Password:"
send "FrogsHealth@1\r"

interact
