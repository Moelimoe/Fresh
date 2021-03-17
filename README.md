# Fresh
Fresh is an online B2B projects.

Fresh是一个能实现在高流量，海量数据和高并发访问情况下保证正常并兼顾速度运行的Web型线上商城网站  

主要使用的技术有：    

1.使用了扩展性好和存储可靠的集群式服务器fastdfs，结合nginx实现页面内容静态化加快用户二次访问的速度，可实现大量用户访问依然保证服务器性能；  
2.使用MySQL作为数据后台存储服务器，使用了redis作为MySQL的高速缓存，用户在获取和存储大部分数据时可以不用访问对MySQL做出查询和修改，一定程度减少了后台数据库的压力  
3.使用了celery的异步处理技术，使一些响应时间较长的任务，例如注册时邮件发送、首页大量图片的展示（在celery服务器配置nginx），在用户点击提交后依然可以很快的得到响应  
4.前端js使用一些ajax异步处理方法，减轻了服务器压力，直接式响应提升了用户体验  
5.利用了MySQL事务的特点处理高并发情况下的订单提交问题  



文件目录结构如下：  
├─.idea  
│  └─inspectionProfiles  
├─apps  
│  ├─booktest  
│  │  └─__pycache__  
│  ├─cart  
│  │  ├─migrations  
│  │  │  └─__pycache__  
│  │  └─__pycache__  
│  ├─goods  
│  │  ├─migrations  
│  │  │  └─__pycache__  
│  │  └─__pycache__  
│  ├─order  
│  │  ├─migrations  
│  │  │  └─__pycache__  
│  │  └─__pycache__  
│  ├─user  
│  │  ├─migrations  
│  │  │  └─__pycache__  
│  │  └─__pycache__  
│  ├─utils  
│  │  ├─fdfs  
│  │  │  └─__pycache__  
│  │  └─__pycache__  
│  └─__pycache__  
├─celery_tasks  
│  └─__pycache__  
├─dailyfresh  
│  └─__pycache__  
├─db  
│  └─__pycache__  
├─logfiles  
├─static  
│  ├─css  
│  ├─df_goods  
│  ├─html_bk  
│  ├─images  
│  │  └─goods  
│  └─js  
├─templates  
│  └─search  
│      └─indexes  
│          └─goods  
├─whoosh_index  
└─__pycache__  
  


