import torch
import torch.nn as nn


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim=17, hidden_dim=32, latent_dim=8, num_layers=1):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.enc_fc  = nn.Linear(hidden_dim, latent_dim)
        self.dec_fc  = nn.Linear(latent_dim, hidden_dim)
        self.decoder = nn.LSTM(hidden_dim, input_dim, num_layers, batch_first=True)

    def forward(self, x):
        _, (h, _) = self.encoder(x)
        z         = self.enc_fc(h[-1])
        dec_in    = self.dec_fc(z).unsqueeze(1).repeat(1, x.size(1), 1)
        out, _    = self.decoder(dec_in)
        return out, z

    def reconstruction_error(self, x):
        out, _ = self.forward(x)
        return torch.mean((x - out) ** 2, dim=(1, 2))