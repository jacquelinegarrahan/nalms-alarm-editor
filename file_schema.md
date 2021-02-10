# Configuration File Schema

The Phoebus configuration files are in xml format with a "config" root element, "component" group elements, and "pv" pv elements.


## PV
description: str  
enabled: true/false  
latching: true/false  
annunciating: true/false  
delay: int  
count: int  
filter: str  
command

## GROUP
automated_action

### automated_action
title: str    
details: str    
delay: int  

### command
title: str  
details: str  
