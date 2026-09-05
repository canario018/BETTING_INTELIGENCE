# BLOCO 13 — Expansão de APIs, Qualidade e Saúde dos Coletores

## Objetivo

O BLOCO 13 amplia o sistema com cinco novas fontes fornecidas no projeto e uma sexta integração Altenar:

- R7Bet
- Onabet
- VBET
- Bet.Bet
- 7KBet
- ApostaGanha permanece na arquitetura Altenar

Além disso, a saúde dos coletores passa a medir não apenas HTTP/latência, mas também qualidade básica dos registros normalizados.

## Fontes adicionadas

### R7Bet
Endpoint fornecido no projeto:
`https://r7.bet.br/api/sportsbook/data/v1/sportsdata/featured/events`

Parâmetros:
`featureTag=all`, `sportIDs=1`, `includeMarkets=default`, `take=50`, `skip=0`, `locale=br-pt`.

### Onabet
Endpoint Altenar:
`https://sb2frontend-altenar2.biahosted.com/api/widget/GetCouponEvents`

Integração: `onabet`.

### VBET
Endpoint fornecido no projeto:
`https://www.vbet.bet.br/desktop/pageBuilder/sport.json`

Observação: este endpoint pode retornar configuração/estrutura de página em vez de odds diretamente. O sistema não inventa odds; se não houver preço identificável, o health será `EMPTY`.

### Bet.Bet
Endpoint fornecido no projeto:
`https://betpontobet.bet.br/api/sports/rogue-proxy/v1/sportsdata/events`

Parâmetros: `take=50`, `orderBy=leagueOrder`, `includeMarkets=default`, `eventType=Fixture`, `sportIDs=1`.

### 7KBet
Endpoint fornecido no projeto:
`https://prod20350-kbet-152319626.fssb.io/api/sportscenter/carousels/events-with-items`

## Importante sobre validação

Os endpoints acima foram incorporados exatamente como fornecidos. Isso não significa que todos os endpoints estarão disponíveis ou que todos terão a mesma estrutura em cada execução.

O sistema agora diferencia:

- `OK`: resposta HTTP válida e odds normalizadas;
- `EMPTY`: resposta válida, mas nenhuma odd foi identificada pelo parser;
- `ERROR`: falha HTTP, JSON, timeout ou outra exceção.

## Qualidade

O health calcula:

- quantidade de registros;
- eventos únicos;
- taxa de duplicidade;
- percentual sem horário de início;
- percentual de mercados suportados;
- score de qualidade básico;
- HTTP status;
- bytes da resposta;
- latência;
- endpoint.

O score é diagnóstico, não é uma garantia de qualidade estatística.

## Coletores ativos

No `.env`:

```env
COLLECTORS=estrelabet,lotogreen,multibet,onabet,r7bet,betbet,vbet,7kbet
```

Para testar primeiro de forma controlada, use apenas as casas desejadas, por exemplo:

```env
COLLECTORS=estrelabet,onabet,r7bet,betbet,7kbet
```

## Validação do pacote

Testes automatizados: **43 passed, 5 warnings**. Os warnings são dos testes históricos que ainda usam `datetime.utcnow()`.

## Próximo passo

Depois de confirmar quais fontes retornam odds reais, o próximo avanço deve ser melhorar os parsers específicos das APIs que retornarem `EMPTY`, usando o JSON bruto salvo em `data/raw/`. Isso evita adivinhar estruturas.
