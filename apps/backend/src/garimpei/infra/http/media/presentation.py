from garimpei.domain.listing.exploration import Offer
from garimpei.domain.media.media import MediaGallery


def media_context(offer: Offer, recovery_url: str) -> dict[str, object]:
    gallery = offer.media
    photos = (
        tuple(
            dict(
                photo=p,
                original=f"/ofertas/{offer.id}/imagens/{p.version_id}/original/",
                thumbnail=f"/ofertas/{offer.id}/imagens/{p.version_id}/miniatura/",
            )
            for p in gallery.photos
            if p.version_id
        )
        if gallery
        else ()
    )
    label = gallery_label(gallery, bool(photos))
    return dict(
        media_gallery=gallery,
        media_photos=photos,
        media_primary=photos[0] if photos else None,
        media_label=label,
        media_recovery=recovery_url,
    )


def gallery_label(gallery: MediaGallery | None, photos: bool) -> str:
    if gallery is None:
        return "Fotos ainda não verificadas"
    label = "Fotos ainda não verificadas"
    if gallery.presence == "none":
        return "Anúncio sem fotos na fonte"
    if gallery.state == "configuration_required":
        return (
            "Fotos ainda não verificadas; obtenção aguarda configuração do armazenamento"
            if gallery.presence == "unknown"
            else "Fotos aguardam configuração do armazenamento"
        )
    if gallery.state in {"pending", "running"} and gallery.presence != "unknown":
        return "Obtenção de fotos pendente"
    if gallery.state == "failed":
        return "Falha na obtenção de fotos"
    if gallery.state == "partial":
        return "Coleta de fotos parcial; cópias anteriores conservadas quando disponíveis"
    if photos:
        return "Fotos conservadas neste computador"
    return label
