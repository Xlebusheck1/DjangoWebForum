class CentrifugeClient {
    constructor(wsUrl, token) {
        this.wsUrl = wsUrl;
        this.token = token;
        this.client = null;
        this.subscriptions = {};
    }

    connect() {
        this.client = new Centrifuge(this.wsUrl, {
            token: this.token
        });

        this.client.on('connect', function(ctx) {
            console.log('Centrifuge connected');
        });

        this.client.on('disconnect', function(ctx) {
            console.log('Centrifuge disconnected');
        });

        this.client.connect();
    }

    subscribe(channel, token, handlers) {
        if (this.subscriptions[channel]) {
            return;
        }

        const sub = this.client.newSubscription(channel, {
            token: token
        });

        sub.on('publication', function(ctx) {
            if (handlers.onPublication) {
                handlers.onPublication(ctx.data);
            }
        });

        sub.on('subscribing', function(ctx) {
            console.log(`Subscribing to ${channel}`);
        });

        sub.on('subscribed', function(ctx) {
            console.log(`Subscribed to ${channel}`);
        });

        sub.subscribe();
        this.subscriptions[channel] = sub;
    }

    disconnect() {
        if (this.client) {
            this.client.disconnect();
        }
    }
}