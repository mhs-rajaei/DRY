# DRY
#### DRY: Don’t Repeat Yourself (Merge, Extend and Override your config file)

This code can handle dictionary like formats, like YAML, JSON, INI, XML, etc.
You can follow below example to find out how the code works.

---
#### Tested by python 2.7.15 and python 3.6.8 and 3.7.1
##### Working with python >= 2.7.x and python >= 3.6.x

To ease of use some requirements added to libs.

#### References:
 ##### flatdict (https://pypi.org/project/flatdict/)
 ##### melddict (https://pypi.org/project/melddict/)
melddict work with python 2.7.x and work in windows!
---
### Demo configuration in yaml
##### By default we use '(&anchor_key)' as anchor name. anchor name can be a combination of the: 'a-z' or 'A-Z' or '_' or '.'
##### You can use you anchor pattern by re_anchor, re_name and anchor_start_patter in DRY.
```python
re_anchor = r'\([\&][a-zA-Z\._0-9]{1,}\)'
re_name = r'[a-zA-Z\._0-9]{1,}'

merger_obj = ConfigMerger(config_dict, merge_at_init, re_anchor=re_anchor, re_name=re_name, anchor_start_pattern='(&', pointer_pattern='->', delimiter=':')
```
##### config_dict: input dictionary for do merging.

##### re_anchor: regex for extracting anchor from dictionary key. This regex do something like: 'key_name(&anchor_name)' -> '(&anchor_name)')

##### re_name: regex for extracting name of anchor(s) or pointer(s).

##### anchor_start_pattern: pattern of starting anchor for splitting key by that. by '(&' as anchor pattern and doing split, we have: key_name(&anchor_name)' -> ['key_name' , 'anchor_name']

##### pointer_pattern: string pattern for find pointers in dictionary keys. this pattern must never be used as name of keys that we don't want to be a pointer. just use this pattern in where that you wanna have a pointer.
##### For the duplicate name of this pattern in the same key, you can add any string to this pattern.
```yaml
   ->1: pointer1
   ->2: pointer2
```
###### We do something like this:
```python
if pointer_pattern in key:
    add the value of this key to pointers.
```
##### delimiter: separator in flatten dictionary, default delimiter is ':'
---
### Notes:
##### Don't use a pointer as a list value(element), because we don't merge this pointer.

##### By default we use '->' as pointer notion of anchor key. If you want to use multiple pointers in one key, you can add any string to pointer notion.

##### Do not use pointer notion in the names of other keys unless you want this key to be a pointer to an anchor.
##### Key Name cant start with anchor_start_pattern

##### Lengtg name of Key must be greater than zero
##### Anchor must be end of key name

##### Anchors must be unique

##### Pointers must match to the anchors

Priority in multiple pointers is: from newest to oldest, As Example:
```yaml
key_name(&anchor_1):
  ...
key_name(&anchor_2):
  ...
key_name(&anchor_3):
  ...
```
###### For this example we fist of all merge 'anchor_3' then 'anchor_2' and finally 'anchor_1'.

##### In following everywhere that an anchor set by an anchor name, we call this key as an anchor and everywhere a pointer notion used we call the parent of this key as a pointer
```yaml
database:
  mysql(&mysql_anchor):
    location: mysql-db-prod
    pass: dsf#@4DdfdsF$FE{PHLG{FV+_>+Z>qDwcwEF$Wg64VM VNEPCKCPQ#_DXPJMQ#M

    apiVersion: v1
    kind: Service
    metadata:
      name: mysql
      labels:
        "heptio.com/example": lamp
    spec:
      type: ClusterIP
      ports:
        port: 3306
        protocol: TCP
      selector:
        app: mysql

  mongo_db(&mongodb_anchor):
    storage:
      dbPath: /data/db
      engine: wiredTiger
      wiredTiger:
        engineConfig:
          cacheSizeGB: 8
        collectionConfig:
          blockCompressor: snappy
    systemLog:
      destination: file
      path: /var/log/mongodb.log
      logAppend: true
      timeStampFormat: iso8601-utc
    replication:
      oplogSizeMB: 10240
      replSetName: rs1
    processManagement:
      fork: true
    net:
      bindIp: "192.0.2.1,127.0.0.1"
      port: 27018
    security:
      keyFile: data/key/rs1.key
      authorization: enabled
    sharding:
      clusterRole: shardsvr

  redis(&redis_anchor):
    parameters:
      redis.default.host: tcp://1.2.3.4:6789/1
      redis.default.password: azerty123
      redis.some_cluster.host:
        - 'tcp://1.2.3.4:30001'
        - 'tcp://2.3.4.5:30002'
    client:
      default:
        host: "%redis.default.host%"
        type: phpredis
        password: "%redis.default.password%"
        persistent: true

      some_cluster:
        host:
          - 'tcp://1.2.3.4:30001'
          - 'tcp://2.3.4.5:30002'
        type: phpredis
        cluster: true
        failover: 1

applications:
  app_1:  # Adding from anchor
    # this app use mysql
    ->: mysql_anchor  # Here we add 'mysql' with all child's in 'app_1'
    name: app_1
    module: mapp_1

  app_2:  #  Adding and override values of the pointer for same keys in an anchor
    name: app_2
    ->: mongodb_anchor
    # override below settings, if you add some key that exist in anchor DRY first add anchor child's then merge for same keys. If same key have
    # same child's DRY set below setting as values. Keys in 'app_2' have fisrt priority in merging, that's mean value of 'app_2' keys with
    # same name will set.
    systemLog:
      destination: new_file
      path: "/etc/my_log/mongodb_app_2.log"
      logAppend: False
      timeStampFormat: Simple
      replication:
        oplogSizeMB: 14853
        replSetName: "rs5"
      processManagement:
        fork: False

  app_3:  # Add new kay/values and overriding new keys from pointer to the anchor
    ->: redis_anchor
    name: app_3

    parameters:
      redis.default.host: udp://100.214.30.45:7899/9
      redis.my_new_key: somestring
      client:
        default:
          host: localhost

        some_cluster:
          host:
            - 'tcp://5.6.7.8:50007'
            - 'tcp://7.8.9.10:40255'
          type: phpredis
          cluster: False
          new_key:
           new_child: somevlue
           new_child_2:
             new_new_child:
               - value_1
               - value_2
               - value_3

  app_4: # Add multiple pointers to the multiple anchors
    name: app_4
    ->: redis_anchor
    ->_1: mysql_anchor
    ->_2: mongodb_anchor
    # Priority of merging is from pointer to '->_2' to '->_1' and at the edn: '->'. This priority means if same key exist in this
    # pointer or anchors, value of pointer set as final value after merging, then '->-2'  to '->_1' to '->'
```
---
### Usage

#### Clone repository
##### pip install -r requirements.txt
##### copy files to your project

```python
from DRY import ConfigMerger

# Loading config in YAML format
config_dict = load_from_yaml('config.yaml')
    
# Usage of DRY
merger_obj = ConfigMerger(config_dict, merge_at_init=True)

# Get merged dict as result
merged_config_dict = merger_obj.config_dict
```
    
