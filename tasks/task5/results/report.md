## Отчет о проделанной работе

- Сервис из задачи 4 адаптирован для двух версий; в ответы добавлен заголовок версии.
- Добавлены Gateway и VirtualService с канареечной маршрутизацией 90/10 и fallback-маршрутом через общий пул сервиса при остановленной v1.
- В DestinationRule настроены подмножества v1/v2 и Circuit Breaking, в VirtualService — Retry.
- Добавлен EnvoyFilter для фича-флага X-Feature-Enabled: true с направлением запросов в v2.
- В Helm-шаблоны добавлены общая метка приложения и метки версий, подготовлены отдельные конфигурации v1/v2.
- Обновлены скрипты проверки canary, feature flag и fallback: версия определяется по заголовку ответа, ошибки учитываются явно. Доступ выполняется через ingressgateway с пробросом на порт 9090.

## Запуск

Команды выполнять из каталога задачи.

```sh
minikube start --driver=docker
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled --overwrite
docker build -t booking-service:task5 booking-service
minikube image load booking-service:task5

helm upgrade --install booking-service-v1 helm/booking-service -n default -f helm/booking-service/values-v1.yaml
helm upgrade --install booking-service-v2 helm/booking-service -n default -f helm/booking-service/values-v2.yaml --set service.enabled=true
kubectl apply -f results/gateway.yaml -f results/destination-rule.yaml -f results/virtual-service.yaml -f results/envoy-filter.yaml
kubectl rollout status deployment/booking-service-v1 -n default
kubectl rollout status deployment/booking-service-v2 -n default
kubectl -n istio-system port-forward svc/istio-ingressgateway 9090:80
```

## Проверки

Оставить проброс порта работающим, в другом терминале:

```sh
bash check-istio.sh
bash check-canary.sh
bash check-feature-flag.sh

kubectl scale deployment booking-service-v1 -n default --replicas=0
bash check-fallback.sh
```

Для canary ожидается приблизительно 90/10, для feature flag и fallback при остановленной v1 — успешные ответы v2.
