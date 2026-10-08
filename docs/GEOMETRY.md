# Geometria local

Fonte: [ESA Navipedia, Transformations between ECEF and ENU coordinates](https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates), J. Sanz Subirana, J. M. Juan Zornoza e M. Hernández-Pajares (2011), equações 6 e 8–11. Consultada em 08/10/2026.

Primeiro convertemos as coordenadas para metros e calculamos ΔXYZ = XYZsat − XYZest. A matriz da equação 6 fornece E, N, U. Usamos azimute = atan2(E,N) normalizado para [0,360) e elevação = atan2(U,√(E²+N²)), em graus. Estas formas preservam os quadrantes e evitam divisão por zero.

É obrigatório informar separadamente as unidades da estação e do satélite (`m` ou `km`), a latitude geodética, a longitude e a máscara em graus. São parâmetros do usuário, não informações confirmadas dos arquivos. Esta etapa não calcula latitude/longitude de XYZ nem confirma datum ou consistência entre esses parâmetros.

Quadrantes são uma convenção do projeto: NE [0,90), SE [90,180), SO [180,270), NO [270,360). No zênite/nadir o azimute e o quadrante ficam vazios. A tolerância horizontal relativa de 1e-12 evita direções artificiais por arredondamento; é uma tolerância computacional sem unidade, não um limiar de cintilação.

A máscara é inclusiva (`elevação >= mínimo`) e apenas marca observações; não as remove. O valor 30° foi solicitado no texto do projeto e continua pendente de conferência contra o plano original. Nenhum perfil é ativado automaticamente.

## Execução

Após confirmar os parâmetros da estação e as unidades, acrescente ao comando do guia:

```text
--station-unit m --satellite-unit km --latitude LATITUDE --longitude LONGITUDE --minimum-elevation 30
```

Substitua LATITUDE e LONGITUDE pelos valores geodéticos documentados. As unidades acima são exemplo de sintaxe, não confirmação sobre os .SUM. `geometry.csv` associa cada resultado ao arquivo e linha original e registra todos os parâmetros de entrada. Valores abaixo do horizonte são preservados. Direção de alcance zero ou coordenadas não finitas provocam erro explícito antes da escrita dos produtos.

Os testes usam direções cardinais analíticas, zênite/nadir, rotação de longitude, unidades distintas e limites dos quadrantes e da máscara. Validação com a estação e noites reais continua pendente.
