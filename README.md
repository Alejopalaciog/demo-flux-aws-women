# ¿GitOps en AWS? Infraestructura sincronizada para EKS

![FluxCD drawio](https://github.com/user-attachments/assets/d29f6758-94ea-47b8-ba77-be996ae6b9ad)

### Prerrequisitos
- **Cuenta de AWS**
- **Cuenta de GitHub**
- **AWS CLI**
- **Kubectl**
- **Docker**
- **Autenticacion mediante AWS CLI**

### Links útiles
- [Modulo de Terraform para EKS](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
- [Instalación oficial de FluxCD](https://fluxcd.io/flux/installation/)
- [Multi-cluster Setup](https://fluxcd.io/flux/get-started/#multi-cluster-setup)

## Comencemos con la instalación

### Creación y autenticación

Necesitamos instalar la CLI de flux para poder interactuar con sus recursos, para esto ejecutamos el siguiente comando:

```zsh
curl -s https://raw.githubusercontent.com/fluxcd/flux2/main/install/flux.sh | sudo bash
```

![image](https://github.com/user-attachments/assets/d77bed71-9cf3-43a5-b77e-8aac8e9c7c2a)


Posterior a esto debemos crear nuestro cluster de EKS, en nuestro caso vamos a hacer uso de terraform, especificamente el modulo oficial de EKS pero se pueden implementar diferentes estrategias para hacerlo.
Definimos el archivo .tf donde definimos nuestra configuracion que nos indica la documentacion del modulo y hacemos `terraform apply`

![image](https://github.com/user-attachments/assets/fbf5a785-b9a9-49fd-8e74-b272d84f52f1)

Y actualizamos el contexto de trabajo para poder ejecutar comandos sobre nuestro cluster

```zsh
aws eks update-kubeconfig --name
```

![image](https://github.com/user-attachments/assets/2b429878-8e46-4fae-958c-4bcc00873f4b)

Teniendo nuestro cluster creado y el contexto definido podemos realizar un chequeo de prerequisitos para validar que se pueda instalar Flux en nuestro cluster

```zsh
flux check --pre
```

![image](https://github.com/user-attachments/assets/8cab52e7-43ab-48cc-9c1a-cc5e46dbae24)

Ahora necesitamos obtener el PAT (Personal Access Token) de Github donde vamos a tener nuestro codigo de la infraestructura, la ruta para crearlo es Settings / Developer Settings / Personal Access Tokens / Token (classic)

![image](https://github.com/user-attachments/assets/a0f10af8-3216-4e3b-83e3-66107a476d0a)

Y exportamos este token como variable de entorno `export GITHUB_TOKEN= ghp_`
![image](https://github.com/user-attachments/assets/b0e3a493-897a-4e0e-b078-04c1859752cd)

### Bootstraping de Flux

Ahora con nuestros recursos creados y autenticados procederemos a hacer el bootstraping de Flux de la siguiente manera:

```zsh
flux bootstrap github \
  --owner=GITHUB_USER \
  --repository=REPOSITORY \
  --branch=main \
  --path= ./PATH_TO_INFRA \
  --personal
```

Reemplazamos valores y ejecutamos

![image](https://github.com/user-attachments/assets/431c3ff9-6e8b-4505-b423-8f23dca66162)

Este comando nos va a crear los manifiestos de los controladores necesarios para que Flux corra en nuestro cluster, ademas de que aplica estos cambios, realiamos `kubectl get all -n flux-system` para validar que tengamos una salida similar a la siguiente:

![image](https://github.com/user-attachments/assets/3b345800-da18-4d81-816b-335f7df37c73)

Ahora chequeamos nuevamente que cumplamos con los prerrequisitos necesarios para crear nuestro webhook que va a sincronizar nuestro codigo de la infraestructura con nuestro cluster

![image](https://github.com/user-attachments/assets/09ed508b-7988-40c6-bcea-b82d91c2eb81)

### Creación del webhook

Procedemos a generar nuestros archivos GitRepository.yml y Kustomization.yml y aplicar estos recursos sobre nuestro cluster `kubectl apply -n default -f .`

*gitrepository.yml*
```yml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: example-app-1
  namespace: default
spec:
  interval: 1m0s
  ref:
    branch: main
  url: https://github.com/Alejopalaciog/demo-flux-aws-women
```

*kustomization.yml*
```yml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: example-app-1
  namespace: default
spec:
  interval: 15m
  path: "./iac/manifest/app"
  prune: true
  sourceRef:
    kind: GitRepository
    name: example-app-1
```
Obteniendo una salida similar a la siguiente:

![image](https://github.com/user-attachments/assets/a99c6763-4154-4c64-9d61-4bc917098df0)


### Creación de la imagen

Para que nuestro contenedor haga ejecucion de nuestra logica necesitamos generar una imagen y almacenarla en un repositorio de imagenes, por lo tanto vamos a crear un repositorio en ECR

![image](https://github.com/user-attachments/assets/1fc5b6b8-0d0e-460e-9b35-ac112cac0313)

Y vamos a hacer un `docker login` para que podamos subir nuestras imagenes desde nuestra maquina

```zsh
aws ecr get-login-password --region region | docker login --username AWS --password-stdin aws_account_id.dkr.ecr.region.amazonaws.com
```

![image](https://github.com/user-attachments/assets/c5b547ff-3e0c-461e-933b-f295aaa2dfb9)

Luego realizamos un `docker build` y `docker push`

```zsh
docker build -t 314876856196.dkr.ecr.us-east-1.amazonaws.com/demo-flux-aws-women/example-app:0.0.1
```

![image](https://github.com/user-attachments/assets/e57ac8a6-fc2c-489f-b4f0-52aa085be9fe)

```zsh
docker push 314876856196.dkr.ecr.us-east-1.amazonaws.com/demo-flux-aws-women/example-app:0.0.1
```

![image](https://github.com/user-attachments/assets/a7b267e9-23ff-44bd-8de0-ec2631918e4e)

### Instanciación de la infraestructura de la aplicación

Realizamos `kubectl apply -n default -f .` sobre la ruta donde tenemos nuestros manifiestos de la aplicación

![image](https://github.com/user-attachments/assets/ce629e71-a54e-46be-af0f-ef6bb63202e8)

Y procedemos a obtener su balanceador de carga para probarla

![image](https://github.com/user-attachments/assets/9f114d9f-1e7c-41d3-9fcf-b67c94c813c8)

![image](https://github.com/user-attachments/assets/d2353e40-c12f-4839-a5a8-2b657a7ce5c2)

De esta manera podemos crear una correcta integracion de FluxCD con nuestra infraestructura alojada en EKS de AWS

## Estrategías
### Base strategy

![Diagrama sin título-FabricaPequeñaMediana](https://github.com/user-attachments/assets/d8f5a101-056c-4237-bff2-69983b1538a4)

### Big strategy
![Diagrama sin título-FabricaGrande](https://github.com/user-attachments/assets/239a77f3-a28b-4fba-8e0d-deccc36c0265)
