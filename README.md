# AI-Dental-Health-APP
Project for MediaTek's digital social innovation competitions "Genius for home"

## Overview
A backend service for detecting the percentage of dental plaque on teeth.

## API Documentation

#### Invoke API server to check server is running:

- Request:
```
[GET] /api/ping/
```

- Response:
```
{
    "message": "Hi there, API is working~"
}
```

#### Send image to API for detecting dental plaque:

- Request:
```
[POST] /api/analysis/
key: image
value: png file
```
- Response:
```
{
    "message": "The percentage of dental plaque on teeth: 43.08%",
    "data": {
        "teethRangePath": "teeth_range/2024-08-04_23-42-30/",
        "teethRangeDetectPath": "teeth_range_detect/2024-08-04_23-42-30/"
    }
}
```

#### Get teeth_range image from API:

- Request:
```
[GET] /api/analysis/teeth_range/2024-08-04_23-42-30/
```
- Response:
```
the png file of teeth_range
```

#### Get teeth_range_detect image from API:

- Request:
```
[GET] /api/analysis/teeth_range_detect/2024-08-04_23-42-30/
```
- Response:
```
the png file of teeth_range_detect
```


## Using AI-Dental-Health-APP service with Docker
*Please ensure the weight files are stored in the project directory.*\
Download link of weight files: \
https://github.com/YYinBigBang/AI-Dental-Health-APP/releases/tag/weight1.0

#### Build image:
```docker
docker build -t ai_dental_health_app .
```

#### Run container:
```docker
docker run -p 8000:8000 -e PORT=8000 ai_dental_health_app
```

#### To obtain the SSL certificates for the first time, run Certbot directly:
```docker
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d your_domain_or_ip --email your_email@example.com --agree-tos --no-eff-email
```

#### Start all the Services with docker-compose:
```docker
docker-compose up -d
```

#### Rebuild Docker image and start container:
```docker
docker-compose up --build
```

#### Delete Docker container:
```docker
docker-compose down
```

#### Delete Docker image and data:
```docker
docker system prune -a --volumes
```

#### List containers:
```docker
docker ps
```

#### Enter container:
```docker
docker exec -it [container name or ID] bash
```

#### Delete containers and images:
```docker
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi $(docker images -q)
```

---

### Improvements:
> 1.Implement LineBot (webhook)

> 2.Transfer file access functionality to model.py (on going)

> 3.Implement a new feature for API return code
  - `returncode -> 0` API success.
  - `returncode -> 1` Teeth not detected.
  - `returncode -> 2` Dental plaque not detected.
  - `returncode -> 3` Invalid image format.
  - `returncode -> 4` API internal error.
  - `returncode -> 5` Unauthorized access.

> 4.Implement a new feature for JWT (API token)
