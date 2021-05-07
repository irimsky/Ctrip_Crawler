# Ctrip_Crawler 携程景点爬虫



![image-20210313235926448](https://irimskyblog.oss-cn-beijing.aliyuncs.com/content/20210313235929.png)



![image-20210314000428177](https://irimskyblog.oss-cn-beijing.aliyuncs.com/content/20210314000432.png)



- 爬取的是 [**携程移动端**](https://m.ctrip.com/webapp/you/gspoi/sight/1.html?seo=1) 的数据（景点数据以及评论）

- 修改`config.ini`中的配置可以改变**目标城市**（默认北京）以及**爬取模式**

    ![](https://irimskyblog.oss-cn-beijing.aliyuncs.com/content/20210507163603.png)

    

- 爬取结果有两部分：`data/poi.csv`为**景点数据**，`data/comment/{id}.csv`为对应ID的景点的**评论数据**

- 评论内容的爬取有两种方法：
  - 将`config.ini`中的`isCrawlComment`置为1，运行`poi_crawl.py`文件，在爬取 景点数据 的过程中爬取 评论数据 
  - 将`config.ini`中的`isCrawlComment`置为0，运行`poi_crawl.py`文件，在爬取 景点数据 结束后运行再运行`comment_crawl.py`文件，获取 景点数据 中的所有景点的评论
  
- 每次运行前都会在同一文件夹下复制一份上一次爬取的景点结果的备份，名为`back.csv`

- 数据中 **价格**、**最低价格**为response中的数据，暂无参考价值

- 后面四种人群门票价格为**预估的销量加权平均价格**，如果有不同需求可以修改 `GetTicketPrice` 函数。（返回的数据为所有的门票价格）

- 景点数据中的**开放时间**与**优惠政策** 数据的格式为json格式

- 爬取的 评论数据 格式为：

    - **用户ID**
    - **评论文本**
    - **发送时间戳**
    - **赞同数**

TODO： 

后续可能会支持：

输入城市名称自动获取城市编号 （√）
如果上次爬取过程中断可以从断点处开始爬取 （√）