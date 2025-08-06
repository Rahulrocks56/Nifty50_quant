    fig.add_trace(go.Scatter(
        x=indicators_df['timestamp'],
        y=indicators_df['BB_lower'],
        name='Lower Band',
        line=dict(color='green', dash='dash'),
        fill='tonexty'
    ))
    
    fig.update_layout(
        title='Price with Bollinger Bands',
        xaxis_title='Time',
        yaxis_title='Price'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display latest indicator values
    st.subheader("Latest Indicator Values")
    st.write(f"RSI: {indicators_df['RSI'].iloc[-1]:.2f}")
    st.write(f"ADX: {indicators_df['ADX'].iloc[-1]:.2f}")
    st.write(f"Aroon Up: {indicators_df['Aroon_Up'].iloc[-1]:.2f}")
    st.write(f"Aroon Down: {indicators_df['Aroon_Down'].iloc[-1]:.2f}")
    st.write(f"MACD: {indicators_df['MACD'].iloc[-1]:.2f}")
st.caption(f"Last updated: {st.session_state.live_data['timestamp']}")
