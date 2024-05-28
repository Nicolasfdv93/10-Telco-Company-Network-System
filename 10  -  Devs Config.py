Project 10  - Telco Company Network System

//Note: We don’t have control over SEACOM ISP and AZURE CLOUD Routers, they are managed by the providers. 

Cisco WLC config
1.	Access from Sr. Engineer PC’s browser and type IP MGMT of WLC. 10.20.0.10 in this case
2.	Create an User and Passwd – In this case Cisco / Cisco123
3.	Configure Basics settings + IP/MASK MGMT + Default GW
4.	Create WLANS: Employees and Guests WiFi with SSID / PASS. Employees-WiFi/Cairo123 ; Guests-WiFi/Guests123 ; Respectively.
5.	After the auto-reset of device, login with new configurations. Include in this case https:// prefix of IP. 


### ROUTERS & L3 SW ###
## ALL ROUTERS – Except Firewall ##
	
En
Conf t
Banner motd ** NO AUTHORIZED ACCESS IS PUNISHABLE BY LAW  **
Enable password cisco
Username cisco password cisco
Service password-encryption
Ip domain-name cisco.net
Line console 0
Password cisco
No ip domain-lookup
Crypto key generate rsa
1024
Line vty 0 15
Login local
Transport input ssh
Ip ssh version 2
Exit

Do wr

# CAIRO CORE SW #
// VLAN config: Cisco Wireless LAN Controller should be in the same VLAN as the LAP accces points.
// Also, port to Router-Voice-GW must be trunk, because all IP-Phones will get there.

En
Conf t
Hostname CAIRO CORE-SW
Vlan 50
Name LAN
Vlan 60
Name WLAN
Vlan 99
Name native
Vlan 101
Name VOIP
Exit

Int g1/0/7
No shut
Switchport mode access
Switchport access vlan 60

Int g1/0/8
No shut
Switchport mode trunk
Switchport trunk native vlan 99
Exit

//Int g1/0/9 is working as L3, so it wont use any related VLAN protocol

Int g1/0/9
No switchport
Ip address 10.30.30.2 255.255.255.252

Int ran gig1/0/1-2
No shut
Channel-group 1 mode active
Int port-channel 1
Switchport mode trunk
Switchport trunk native vlan 99
Exit

Int ran gig1/0/3-4
No shut
Channel-group 2 mode active
Int port-channel 2
Switchport mode trunk
Switchport trunk native vlan 99
exit

Int ran gig1/0/5-6
No shut
Channel-group 3 mode active
Int port-channel 3
Switchport mode trunk
Switchport trunk native vlan 99

Int vlan 50
No shut
Ip address 192.168.10.1 255.255.255.0
Ip helper-address 10.10.10.5
Exit

Int vlan 60
No shut
Ip address 10.20.0.1 255.255.0.0
Ip helper-address 10.10.10.5
Exit

//OSPF Configuration. Ref BW: 1GBps
Ip routing
Router ospf 10
Auto-cost reference-bandwidth 1000000
Network 192.168.10.0 0.0.0.255 area 0
Network 10.20.0.0 0.0.255.255 area 0
Network 10.30.30.0 0.0.0.3 area 0
Exit

## FIREWALL ##

Note: Firewalls DENIES all incoming traffic, unless you specify which traffic is allowed. 
En
Conf t
Hostname PERIMETER-FW
Banner motd ** NO AUTHORIZED ACCESS IS PUNISHABLE BY LAW  **
Enable password cisco
Username cisco password cisco
domain-name cisco.net
No ip domain-lookup
Wr mem

//Security levels: Total trust: 100 – Total Untrust: 0
Int gig1/1
No shut
Nameif INSIDE
Security-level 100
Ip address 10.30.30.1 255.255.255.252
Exit

Int gig1/2
No shut
Nameif OUTSIDE
Security-level 0
Ip address 197.200.100.2 255.255.255.252
exit

Int g1/3
No shut
Nameif DMZ
Security-level 70
Ip address 10.10.10.1 255.255.255.240
Exit

// OSPF Configuration. Ref BW: 1GBps. 
// In firewalls the wildcard mask is not issued, you enter the mask instead.

Router ospf 20
Network 10.30.30.0 255.255.255.252 area 0
Network 10.10.10.0 255.255.255.240 area 0
Network 197.200.100.0 255.255.255.252 area 0
Exit

//NAT configuration. In FW you must create objects to create instances of NAT

Object network INSIDE-OUT-LAN
Subnet 192.168.10.0 255.255.255.0
Nat (INSIDE,OUTSIDE) dynamic interface
Exit

Conf t
Object network INSIDE-OUT-WLAN
Subnet 10.20.0.0 255.255.0.0
Nat (INSIDE,OUTSIDE) dynamic interface
Exit

Conf t
Object network INSIDE-OUT-DMZ
Subnet 10.10.10.0 255.255.255.240
Nat (DMZ,OUTSIDE) dynamic interface
Exit

// Default static route towards SEACOM ISP. 
// Routes any traffic that FW doesn’t knows whiche inside network it comes from. 
// So FW sends it to OUTSIDE zone, that is, SEACOM ISP (197.200.100.1).  

Conf t
Route OUTSIDE 0.0.0.0 0.0.0.0 197.200.100.1

// ACLs for inspection policies. Format: permit + protocol + from + to + eq port.
// Ports: DHCP->UDP 67,68. DNS-> UDP 33,TCP 33. ERP (HTTP/S)-> tcp 80, 8080, 443, 8443. EMAIL-> SMTP.
// ACL is applied to the interface named with nameif command. 
// Standard ACL: As close as possible from the destination. Extended ACL: as close as possible from the source. 

Conf t
Access-list INSIDE-DMZ extended permit icmp any any
Access-list INSIDE-DMZ extended permit udp any any eq 67
Access-list INSIDE-DMZ extended permit udp any any eq 68
access-list INSIDE-DMZ extended permit udp any any eq 53
access-list INSIDE-DMZ extended permit tcp any any eq 53
access-list INSIDE-DMZ extended permit tcp any any eq 80
access-list INSIDE-DMZ extended permit tcp any any eq 8080
access-list INSIDE-DMZ extended permit tcp any any eq 443
access-list INSIDE-DMZ extended permit tcp any any eq 8443
access-list INSIDE-DMZ extended permit tcp any any eq smtp
access-group INSIDE-DMZ in interface DMZ 

//ACLs to get resources from AZURE Cloud

Access-list INSIDE-OUTSIDE permit icmp any any
Access-list INSIDE-OUTSIDE permit tcp any any eq 80
Access-list INSIDE-OUTSIDE permit tcp any any eq 8080
Access-list INSIDE-OUTSIDE permit tcp any any eq 443
Access-list INSIDE-OUTSIDE permit tcp any any eq 8443

Access-group INSIDE-OUTSIDE in interface OUTSIDE

Wr mem

## CISCO VOICE GW##
// This router will work as DHCP server for VoIP

En
Conf t
Hostname VoIP-GW
Int fa0/0
No shut
Int fa0/0.101
Encapsulation dot1q 101
Ip address 172.16.10.1 255.255.255.0
Exit
Service dhcp
Ip dhcp pool VoIP
Network 172.16.10.0 255.255.255.0
Option 150 ip 172.16.10.1
Exit

Telephony-service
Max-ephone 15
Max-dn 15
Ip source-address 172.16.10.1 port 2000
Auto assign 1 to 10
Exit
	
//configure one for each existing VLAN

Ephone-dn 1
Number 1001
ephone-dn 2
number 1002
ephone-dn 3
number 1003
ephone-dn 4
number 1004
ephone-dn 5
number 1005
ephone-dn 6
number 1006
exit


## SEACOM ISP ##
En
Conf t
Hostname SEACOM-ISP

Int g0/0
No shut
Ip address 197.200.100.1 255.255.255.252
Exit

Int g0/1
No shut
Ip address 20.20.20.1 255.255.255.252
Exit

Router ospf 30
Auto-cost reference-bandwidth 100000
Network 197.200.100.0 0.0.0.3 area 0
Network 20.20.20.0 0.0.0.3 area 0

Do wr

## AZURE CLOUD ##

En 
Conf t
Hostname AZURE-CLOUD

Int g0/0
No shut
Ip address 20.20.20.2 255.255.255.252
Exit

Int g0/1
No shut
Ip address 30.30.30.1 255.0.0.0 
Exit

Router ospf 40
Auto-cost reference-bandwidth 100000
Network 20.20.20.0 0.0.0.3 area 0
Network 30.30.30.0 0.255.255.255 area 0

### SWITCHES ###

## ALL SWITCHES ##

//Each department has assigned half of the ports of a SW.

En
Conf t
Banner motd ** NO AUTHORIZED ACCESS IS PUNISHABLE BY LAW  **
Enable password cisco
Username cisco password cisco
Service password-encryption
Ip domain-name cisco.net
Line console 0
Password cisco
No ip domain-lookup

//VLAN config: Ports 1-11 & 13-24 -> LAN & VoIP. Ports 12 & 24 -> WLAN

Vlan 50
Name LAN
Vlan 60
Name WLAN
Vlan 101
Name VoIP
Vlan 99
Name native

//Except CAIRO CORE SW

Int ran fa0/1-11
No shut
Switchport mode access
Switchport access vlan 50
Switchport voice vlan 101
Exit

Int fa 0/12
Switchport mode access
Switchport access vlan 60
Exit

Int ran fa0/13-23
Switchport mode access
Switchport access vlan 50
Switchport voice vlan 101
Exit

Int fa0/24
Switchport mode access
Switchport access vlan 60

Exit
Int ran gi0/1-2
Switchport mode trunk
Switchport trunk native vlan 99
Exit

## DMZ-SW ##
En
Conf t
Hostname DMZ-SW

Exit
wr

## CAIRO-ACCESS-SW 1 ##

En
Conf t
Hostname CAIRO-ACCESS-SW1

// LACP & STP Portfast +  BPDUGuard for those EDGE ports (end devices) 

Int ran gi0/1-2
Channel-group 1 mode active
Exit

Int port-channel 1
Switchport mode trunk
Switchport trunk native vlan 99
Exit

Int fa0/24
Spanning-tree portfast
Spanning-tree bpduguard enable

Exit
Do wr

## CAIRO-ACCESS-SW 2 ##
En
Conf t
Hostname CAIRO-ACCESS-SW2

//LACP & STP Portfast +  BPDUGuard for those EDGE ports (end devices) 

Int ran gi0/1-2
Channel-group 2 mode active
Int port-channel 2
Switchport mode trunk
Switchport trunk native vlan 99

Exit
Int fa0/24
Spanning-tree portfast
Spanning-tree bpduguard enable

Exit
Do wr

## CAIRO-ACCESS-SW 3 ##
En
Conf t
Hostname CAIRO-ACCESS-SW3

// LACP & STP Portfast +  BPDUGuard for those EDGE ports (end devices) 

Int ran gi0/1-2
Channel-group 3 mode active
Int port-channel 3
Switchport mode trunk
Switchport trunk native vlan 99
Exit

Int fa0/24
Spanning-tree portfast
Spanning-tree bpduguard enable

Exit
Do wr

