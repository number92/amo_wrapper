
### AmoCRM API v4 Характеристики:
  7 запросов в секунду, не более 250 элементов
### фильтр по дате:

- "updated_at__from": `timestamp`
- "updated_at__to": `timestamp`
- "created_at__from": `timestamp`
- "created_at__to": `timestamp`
- "closed_at__from": `timestamp`
- "closed_at__to": `timestamp`


```
date_from = amoclient.date_to_timestamp(DATE_FROM)
date_to = amoclient.date_to_timestamp(DATE_TO)
await amoclient.get_leads_with_loss_reason(filters=
    {"created_at__from": date_from, "created_at__to": date_to}
)
```


#### Запуск в docker

sudo docker rm --env-file .env -f amocrm-stats && sudo docker rmi -f amocrm-stats
sudo docker build -t amocrm-stats .
sudo docker run --env-file .env -p 10111:10111 -d --name amocrm-stats amocrm-stats