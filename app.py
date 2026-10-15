import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="IPL Analytics Dashboard", page_icon="🏏", layout="wide")
st.markdown("""
<style>
.stApp { background:#080f20; color:#f4f7fb; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#111d3a 0%,#172b57 100%); }
.block-container { padding-top:1.4rem; padding-bottom:2rem; }
h1,h2,h3 { color:#f4f7fb !important; }
.kpi { background:linear-gradient(135deg,#121e3b,#17284c); border:1px solid #293d67; border-radius:14px; padding:17px 19px; min-height:105px; }
.kpi-label { color:#a9bad8; font-size:12px; margin-bottom:8px; }
.kpi-value { color:white; font-size:29px; font-weight:750; }
.kpi-note { color:#8fa7cf; font-size:12px; margin-top:5px; }
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_csv(name): return pd.read_csv(Path(__file__).parent / name)
teams=load_csv('teams.csv'); venues=load_csv('venues.csv'); matches=load_csv('matches.csv')
for df, cols in [(teams,['team_name']),(venues,['venue','city']),(matches,['venue','city','team1','team2','match_winner','season'])]:
    for col in cols:
        if col in df.columns: df[col]=df[col].fillna('').astype(str).str.strip()
# Make sure the supplied names map cleanly to the lookup tables.
team_names=set(teams.team_name)
venue_names=set(venues.venue)

st.sidebar.markdown('## 🏏 IPL ANALYTICS')
st.sidebar.caption('Teams • Venues • Matches')
page=st.sidebar.radio('NAVIGATION',['IPL Overview','Team Analysis','Venue Analysis','Team vs Venue'])
st.sidebar.markdown('---')
st.sidebar.caption('DATASET SUMMARY')
st.sidebar.metric('Teams',len(teams)); st.sidebar.metric('Venue records',len(venues)); st.sidebar.metric('Matches',len(matches))

layout=dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#dbe7fb'),margin=dict(l=15,r=15,t=48,b=15),xaxis=dict(gridcolor='#22314e'),yaxis=dict(gridcolor='#22314e'))
def kpi(label,value,note):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',unsafe_allow_html=True)
def style(fig,height=380):
    fig.update_layout(**layout,height=height)
    return fig

if page=='IPL Overview':
    st.title('🏏 IPL Analytics Dashboard')
    st.caption('Connected analysis of IPL teams, venues, and match records.')
    c1,c2,c3,c4=st.columns(4)
    with c1: kpi('MATCHES',f'{len(matches):,}','Records in matches.csv')
    with c2: kpi('TEAMS',f'{matches.team1.nunique():,}','Teams appearing in matches')
    with c3: kpi('VENUES USED',f'{matches.venue.nunique():,}','Distinct venue names in matches')
    with c4: kpi('SEASONS',f'{matches.season.nunique():,}','Season labels in dataset')
    left,right=st.columns(2)
    with left:
        st.markdown('### Venues Hosting the Most Matches')
        top=matches.groupby('venue',as_index=False).size().rename(columns={'size':'matches_hosted'}).nlargest(10,'matches_hosted').sort_values('matches_hosted')
        fig=px.bar(top,x='matches_hosted',y='venue',orientation='h',color='matches_hosted',color_continuous_scale=['#5eead4','#4387f5'],labels={'matches_hosted':'Matches hosted','venue':'Venue'})
        st.plotly_chart(style(fig),use_container_width=True)
    with right:
        st.markdown('### Matches by Season')
        season_counts=matches.groupby('season',as_index=False).size().rename(columns={'size':'matches'})
        season_counts['season_order']=season_counts['season'].str.extract(r'(\d{4})')[0].fillna('0').astype(int)
        season_counts=season_counts.sort_values('season_order')
        fig=px.line(season_counts,x='season',y='matches',markers=True,labels={'season':'Season','matches':'Matches'},color_discrete_sequence=['#5eead4'])
        st.plotly_chart(style(fig),use_container_width=True)
    st.markdown('### Team Performance')
    played=pd.concat([matches[['team1']].rename(columns={'team1':'team'}),matches[['team2']].rename(columns={'team2':'team'})])
    played_counts=played.groupby('team').size().rename('matches_played')
    wins=matches[matches.match_winner!=''].groupby('match_winner').size().rename('wins')
    perf=pd.concat([played_counts,wins],axis=1).fillna(0).reset_index().rename(columns={'index':'team'})
    perf['win_percentage']=(perf['wins']/perf['matches_played']*100).round(1)
    fig=px.bar(perf.sort_values('wins',ascending=False),x='team',y='wins',color='win_percentage',color_continuous_scale=['#5eead4','#4387f5'],labels={'team':'Team','wins':'Wins','win_percentage':'Win %'})
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(style(fig,420),use_container_width=True)
    st.markdown('### Recent dataset preview')
    st.dataframe(matches[['match_date','season','team1','team2','venue','match_winner']].tail(12),use_container_width=True,hide_index=True)

elif page=='Team Analysis':
    st.title('👥 Team Analysis')
    st.caption('Compare matches played, wins, and win percentage using match records.')
    played=pd.concat([matches[['team1']].rename(columns={'team1':'team'}),matches[['team2']].rename(columns={'team2':'team'})])
    played_counts=played.groupby('team').size().rename('matches_played')
    wins=matches[matches.match_winner!=''].groupby('match_winner').size().rename('wins')
    perf=pd.concat([played_counts,wins],axis=1).fillna(0).reset_index().rename(columns={'index':'team'})
    perf['win_percentage']=(perf['wins']/perf['matches_played']*100).round(1)
    search=st.text_input('Search team',placeholder='Type a team name')
    if search: perf=perf[perf.team.str.contains(search,case=False,na=False)]
    c1,c2,c3=st.columns(3)
    with c1: kpi('TEAMS SHOWN',len(perf),'After search')
    with c2: kpi('TOTAL WINS',int(perf.wins.sum()),'Across displayed teams')
    with c3: kpi('TOP WIN TOTAL',int(perf.wins.max()) if len(perf) else 0,'Among displayed teams')
    fig=px.bar(perf.sort_values('wins',ascending=False),x='team',y='wins',color='win_percentage',color_continuous_scale=['#5eead4','#4387f5'],labels={'team':'Team','wins':'Wins','win_percentage':'Win %'})
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(style(fig,400),use_container_width=True)
    st.dataframe(perf.sort_values('wins',ascending=False),use_container_width=True,hide_index=True)
    st.download_button('⬇️ Download team statistics',perf.to_csv(index=False).encode(),file_name='team_statistics.csv',mime='text/csv')
    st.caption('Win percentage is calculated as wins divided by team appearances (team1/team2 records).')

elif page=='Venue Analysis':
    st.title('🏟️ Venue Analysis')
    st.caption('Use match records to see which grounds hosted the most games.')
    vc=matches.groupby(['venue','city'],dropna=False).size().reset_index(name='matches_hosted').sort_values('matches_hosted',ascending=False)
    search=st.text_input('Search venue or city',placeholder='Type a stadium or city')
    if search: vc=vc[vc.venue.str.contains(search,case=False,na=False)|vc.city.str.contains(search,case=False,na=False)]
    c1,c2,c3=st.columns(3)
    with c1: kpi('VENUES SHOWN',len(vc),'After search')
    with c2: kpi('MATCHES AT SHOWN VENUES',int(vc.matches_hosted.sum()),'Matches represented')
    with c3: kpi('MOST AT ONE VENUE',int(vc.matches_hosted.max()) if len(vc) else 0,'Matches hosted')
    left,right=st.columns([1,1.2])
    with left:
        st.markdown('### Top 10 Venues by Matches Hosted')
        top=vc.nlargest(10,'matches_hosted').sort_values('matches_hosted')
        fig=px.bar(top,x='matches_hosted',y='venue',orientation='h',color='matches_hosted',color_continuous_scale=['#5eead4','#4387f5'],labels={'matches_hosted':'Matches hosted','venue':'Venue'})
        st.plotly_chart(style(fig,450),use_container_width=True)
    with right:
        st.markdown('### Venue table')
        st.dataframe(vc,use_container_width=True,hide_index=True,height=450)
        st.download_button('⬇️ Download venue match counts',vc.to_csv(index=False).encode(),file_name='venue_match_counts.csv',mime='text/csv')

else:
    st.title('🔗 Team vs Venue')
    st.caption('Explore where teams have played, based on the match records.')
    team_list=sorted(set(matches.team1)|set(matches.team2))
    selected=st.selectbox('Choose a team',team_list)
    team_matches=matches[(matches.team1==selected)|(matches.team2==selected)]
    by_venue=team_matches.groupby('venue',as_index=False).size().rename(columns={'size':'matches'})
    c1,c2=st.columns(2)
    with c1: kpi('TEAM MATCHES',len(team_matches),'All listed appearances')
    with c2: kpi('VENUES PLAYED AT',by_venue.venue.nunique(),'Distinct venue names')
    top=by_venue.nlargest(12,'matches').sort_values('matches')
    fig=px.bar(top,x='matches',y='venue',orientation='h',color='matches',color_continuous_scale=['#5eead4','#4387f5'],labels={'matches':'Matches','venue':'Venue'},title=f'{selected}: matches by venue')
    st.plotly_chart(style(fig,470),use_container_width=True)
    st.markdown('### Match records for this team')
    st.dataframe(team_matches[['match_date','season','team1','team2','venue','match_winner','result']],use_container_width=True,hide_index=True)
    st.download_button('⬇️ Download team match records',team_matches.to_csv(index=False).encode(),file_name='team_match_records.csv',mime='text/csv')
